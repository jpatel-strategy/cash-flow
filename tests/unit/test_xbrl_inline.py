from decimal import Decimal

from target_cash.xbrl import parse_inline_xbrl_facts, parse_xbrl_contexts

# Synthetic snippet mimicking the real structure observed in Target's FY2025
# 10-K inline-XBRL markup (see docs/decisions.md, 2026-09-15 entries) — not
# real filing content, just the same shape: xbrli:context blocks plus
# ix:nonFraction elements with varying attribute order.
SYNTHETIC_DOC = """
<xbrli:context id="c-1">
  <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0009999999</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2025-02-02</xbrli:startDate><xbrli:endDate>2026-01-31</xbrli:endDate></xbrli:period>
</xbrli:context>
<xbrli:context id="c-6">
  <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0009999999</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:instant>2026-01-31</xbrli:instant></xbrli:period>
</xbrli:context>
<xbrli:context id="c-seg">
  <xbrli:entity>
    <xbrli:identifier scheme="http://www.sec.gov/CIK">0009999999</xbrli:identifier>
    <xbrli:segment><xbrdi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">us-gaap:RetailSegmentMember</xbrdi:explicitMember></xbrli:segment>
  </xbrli:entity>
  <xbrli:period><xbrli:instant>2026-01-31</xbrli:instant></xbrli:period>
</xbrli:context>

<span><ix:nonFraction unitRef="usd" contextRef="c-6" decimals="-6" name="us-gaap:CashCashEquivalentsAndShortTermInvestments" scale="6" id="f-1">5,488</ix:nonFraction></span>
<span><ix:nonFraction unitRef="usd" contextRef="c-1" decimals="-6" sign="-" name="us-gaap:IncreaseDecreaseInAccountsPayable" scale="6" id="f-2">501</ix:nonFraction></span>
<span><ix:nonFraction contextRef="c-1" unitRef="usd" name="us-gaap:DepreciationAndAmortization" decimals="-6" scale="6" id="f-3">2,617</ix:nonFraction></span>
<span><ix:nonFraction unitRef="usd" contextRef="c-6" decimals="-6" name="us-gaap:DefinedBenefitPlanFairValueOfPlanAssets" format="ixt:fixed-zero" scale="6" id="f-4">&#8212;</ix:nonFraction></span>
<span><ix:nonFraction unitRef="usd" contextRef="c-seg" decimals="-6" name="us-gaap:CashCashEquivalentsAndShortTermInvestments" scale="6" id="f-5">1,200</ix:nonFraction></span>
"""


def test_parse_xbrl_contexts_resolves_duration_context():
    contexts = parse_xbrl_contexts(SYNTHETIC_DOC)
    ctx = contexts["c-1"]
    assert ctx.entity_cik == "0009999999"
    assert ctx.start_date == "2025-02-02"
    assert ctx.end_date == "2026-01-31"
    assert ctx.dimensional_context is None


def test_parse_xbrl_contexts_resolves_instant_context():
    contexts = parse_xbrl_contexts(SYNTHETIC_DOC)
    ctx = contexts["c-6"]
    assert ctx.start_date is None
    assert ctx.end_date == "2026-01-31"
    assert ctx.dimensional_context is None


def test_parse_xbrl_contexts_detects_dimensional_segment():
    contexts = parse_xbrl_contexts(SYNTHETIC_DOC)
    ctx = contexts["c-seg"]
    assert ctx.dimensional_context is not None
    assert "RetailSegmentMember" in ctx.dimensional_context


def test_parse_inline_xbrl_facts_extracts_matching_concepts_only():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:CashCashEquivalentsAndShortTermInvestments"])
    # Two occurrences: one consolidated (c-6), one dimensional (c-seg).
    assert len(facts) == 2
    concepts = {f.concept for f in facts}
    assert concepts == {"us-gaap:CashCashEquivalentsAndShortTermInvestments"}


def test_parse_inline_xbrl_facts_ignores_unrequested_concepts():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:DepreciationAndAmortization"])
    assert len(facts) == 1
    assert facts[0].raw_text == "2,617"


def test_inline_xbrl_fact_value_applies_scale():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:CashCashEquivalentsAndShortTermInvestments"])
    consolidated = next(f for f in facts if f.context.dimensional_context is None)
    assert consolidated.value == Decimal("5488000000")


def test_inline_xbrl_fact_value_applies_negative_sign():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:IncreaseDecreaseInAccountsPayable"])
    assert facts[0].sign_as_reported == -1
    assert facts[0].value == Decimal("-501000000")


def test_inline_xbrl_fact_handles_attribute_order_variation():
    # f-3 has contextRef before unitRef before name — a different order than f-1/f-2.
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:DepreciationAndAmortization"])
    assert facts[0].context_id == "c-1"
    assert facts[0].scale == 6


def test_inline_xbrl_fact_resolves_its_context():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:CashCashEquivalentsAndShortTermInvestments"])
    consolidated = next(f for f in facts if f.context.dimensional_context is None)
    assert consolidated.context.end_date == "2026-01-31"
    assert consolidated.context.start_date is None


def test_inline_xbrl_fact_em_dash_reads_as_zero():
    facts = parse_inline_xbrl_facts(SYNTHETIC_DOC, ["us-gaap:DefinedBenefitPlanFairValueOfPlanAssets"])
    assert facts[0].value == Decimal("0")


def test_parse_inline_xbrl_facts_skips_facts_with_unresolvable_context():
    doc_with_dangling_ref = '<ix:nonFraction unitRef="usd" contextRef="c-missing" name="us-gaap:Foo" scale="6">1</ix:nonFraction>'
    facts = parse_inline_xbrl_facts(doc_with_dangling_ref, ["us-gaap:Foo"])
    assert facts == []


# --- Sign-parsing verification (2026-09-15): the sign attribute is applied ------
# exactly once, never double-negated, never silently converted to an absolute value.

def _single_fact_doc(inner_text: str, *, sign_attr: str = "") -> str:
    sign_part = ' sign="-"' if sign_attr == "-" else ""
    return (
        '<xbrli:context id="c-1"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">'
        "0009999999</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2026-01-31"
        "</xbrli:instant></xbrli:period></xbrli:context>"
        f'<ix:nonFraction unitRef="usd" contextRef="c-1" name="us-gaap:Foo" scale="6"{sign_part}>{inner_text}</ix:nonFraction>'
    )


def test_no_sign_attribute_with_positive_text_reads_positive():
    facts = parse_inline_xbrl_facts(_single_fact_doc("726"), ["us-gaap:Foo"])
    assert facts[0].sign_as_reported == 1
    assert facts[0].value == Decimal("726000000")


def test_sign_minus_with_positive_lexical_text_reads_negative():
    facts = parse_inline_xbrl_facts(_single_fact_doc("940", sign_attr="-"), ["us-gaap:Foo"])
    assert facts[0].sign_as_reported == -1
    assert facts[0].value == Decimal("-940000000")


def test_already_parenthesized_text_with_no_sign_attribute_reads_negative():
    """SEC inline-XBRL practice observed so far always uses sign="-" with plain
    digit text, never literal accounting-style parentheses in the tagged text
    -- but the parser must not crash or misparse if it ever encounters one.
    """
    facts = parse_inline_xbrl_facts(_single_fact_doc("(217)"), ["us-gaap:Foo"])
    assert facts[0].sign_as_reported == 1  # no sign="-" attribute present
    assert facts[0].value == Decimal("-217000000")  # negative from the parentheses alone


def test_parentheses_and_sign_minus_together_do_not_double_negate():
    facts = parse_inline_xbrl_facts(_single_fact_doc("(217)", sign_attr="-"), ["us-gaap:Foo"])
    assert facts[0].value == Decimal("-217000000")  # still just negative, not flipped back to positive


def test_no_silent_absolute_value_conversion():
    """A negative fact's sign must survive unchanged through parsing -- nothing
    in this property path may apply abs() to it."""
    facts = parse_inline_xbrl_facts(_single_fact_doc("940", sign_attr="-"), ["us-gaap:Foo"])
    assert facts[0].value < 0
    assert facts[0].value != abs(facts[0].value)
