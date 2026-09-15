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
