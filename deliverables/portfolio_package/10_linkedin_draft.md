# LinkedIn Draft

---

I spent the last stretch building something I'd wanted to do for a
while: a full, independent cash-flow forecasting and investment-capacity
model for a public company — built entirely from SEC filings, held to
the same standard I'd want from a real strategic-finance deliverable.

A few things I'm genuinely proud of:

📊 **It caught a real accounting reclassification.** Cross-checking
historical figures across filing vintages surfaced a ~$77-92M shift
between cost of sales and SG&A that one company's 10-K quietly made to
two prior years of numbers — with zero revenue or net-income impact,
but a real reason to never trust a single filing's figures in isolation.

🔍 **I found and fixed a real bug in my own model.** An early version of
my "cumulative deployable capacity" calculation was double- and triple-
counting unused cash as it carried forward year to year — overstating
true capacity by roughly 2.6x to 3.8x depending on scenario. I fixed it,
and then built an explicit proof that every dollar of cash generated is
accounted for exactly once, across five possible uses, for every
scenario and year.

📈 **Three scenarios that are actual business stories, not dial-turns.**
Each of Base, Upside, and Downside has its own coherent narrative — the
Upside case, for instance, spends *more* on CapEx, not less, because
funding the growth is what makes the growth possible.

🧮 A restrained, clearly-labeled DCF (not a price target), delivered
across four formats: a live-formula Excel model, a Power BI-ready data
package, and an interactive web dashboard with an editable what-if
sandbox.

✅ 401 automated tests, a from-scratch reproducible rebuild, and a full
decision log recording every judgment call and every bug along the way
— because I think the audit trail is as much the deliverable as the
numbers are.

This was built as a case study, not investment advice — every number
past the most recent filed year is a labeled assumption, not a
prediction. But it's the clearest demonstration I have of how I actually
think about cash, capital allocation, and getting the details right
under real scrutiny.

Happy to walk through it with anyone hiring for FP&A, strategic finance,
or finance-transformation roles.

#FPandA #StrategicFinance #FinancialModeling #CorporateFinance

---

*(Optional: attach a screenshot of the web dashboard's Executive
Snapshot — see `11_screenshot_plan.md` for exactly which one.)*
