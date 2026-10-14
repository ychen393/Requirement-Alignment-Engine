"""Render reviewed structured proposal data as escaped, standalone HTML."""
from html import escape
from requirement_alignment.consulting import ProposalDocument, ProposalBlockType, ProposalStatus


def render_proposal_html(proposal: ProposalDocument, *, allow_draft_preview: bool = False) -> str:
    if proposal.status is not ProposalStatus.APPROVED_FOR_EXPORT and not allow_draft_preview:
        raise ValueError("proposal must be approved for export")
    esc = lambda value: escape(str(value), quote=True)
    parts = []
    for section in sorted(proposal.sections, key=lambda s: s.order):
        blocks = []
        for b in section.blocks:
            if b.type is ProposalBlockType.BULLETS:
                blocks.append("<ul>" + "".join(f"<li>{esc(item)}</li>" for item in b.items) + "</ul>")
            else:
                css = ' class="key-message"' if b.type is ProposalBlockType.KEY_MESSAGE else ""
                blocks.append(f"<p{css}>{esc(b.text or '')}</p>")
        parts.append(f'<section><h2>{esc(section.heading)}</h2>{"".join(blocks)}</section>')
    draft = proposal.status is not ProposalStatus.APPROVED_FOR_EXPORT
    banner = '<aside class="draft">DRAFT PREVIEW — NOT APPROVED FOR CLIENT DELIVERY</aside>' if draft else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{esc(proposal.title)}</title>
<style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#eeece8;color:#282923;font-family:Arial,Helvetica,sans-serif;line-height:1.65}}
main{{max-width:900px;margin:40px auto;background:#fffdf9;padding:clamp(24px,6vw,72px);box-shadow:0 18px 80px #17171716}}
header{{border-bottom:1px solid #cfcac1;padding-bottom:28px}}h1{{font-family:Georgia,serif;font-size:clamp(30px,5vw,52px);line-height:1.15}}h2{{font-family:Georgia,serif;font-size:26px;margin-top:0}}section{{padding:30px 0;border-bottom:1px solid #ebe8e3}}
.label{{letter-spacing:.18em;text-transform:uppercase;font-size:12px;color:#8a7458}}.key-message{{font-weight:bold}}
.draft{{background:#f8ebd7;padding:12px 18px;margin-bottom:28px;font-weight:bold}}
footer{{font-size:12px;color:#716d65;margin-top:32px}}
@media print{{body{{background:white}}main{{box-shadow:none;margin:0;max-width:none}}}}
</style></head><body><main>{banner}<header><div class="label">Consulting Proposal</div>
<h1>{esc(proposal.title)}</h1><p>{esc(proposal.executive_summary)}</p></header>
{"".join(parts)}
<footer>Proposal version {proposal.version_number} · Requirement {esc(proposal.based_on_requirement_version_id)}</footer>
</main></body></html>"""
