"""Render synthetic land document images for the upload demo.

The images are built from the seeded synthetic records, carry a visible
"synthetic sample" watermark and deliberately avoid any government emblem.
Some samples are deliberately forged (they disagree with the records) so the
document cross-check can be demonstrated.
"""
import html
import shutil
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from land.models import Deed, Khatian, Mutation, Person, Plot, TaxRecord
from land.units import share_to_ana
from verification.engine import LAND_CLASS_BN

BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
REPO = Path(settings.BASE_DIR).parent


def bn(value) -> str:
    return str(value).translate(BN)


def esc(value) -> str:
    return html.escape(str(value))


def area(value) -> str:
    return bn(f"{value.quantize(Decimal('0.01')).normalize():f}")


def page(title: str, body: str) -> str:
    font = REPO / "build" / "fonts" / "NotoSansBengali.ttf"
    font_face = f"@font-face{{font-family:Bn;src:url('{font.as_uri()}')}}" if font.exists() else ""
    return f"""<!doctype html><html lang="bn"><head><meta charset="utf-8"><style>
{font_face}
body{{margin:0;background:#fff;font-family:Bn,'Noto Sans Bengali',sans-serif;color:#1d1d1d}}
.page{{box-sizing:border-box;width:940px;margin:20px auto;padding:36px 40px;border:2px solid #333;position:relative;background:#fffef8}}
.wm{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}}
.wm span{{transform:rotate(-24deg);font-size:64px;font-weight:700;color:rgba(180,30,30,.13);white-space:nowrap}}
h1{{text-align:center;font-size:28px;margin:0 0 4px}}
.sub{{text-align:center;font-size:14px;color:#555;margin-bottom:22px}}
.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px 24px;font-size:16px;margin-bottom:22px}}
.meta div{{border-bottom:1px dotted #777;display:flex;justify-content:space-between;padding:3px 0}}
.meta span{{color:#555}}
h2{{font-size:15px;margin:18px 0 6px}}
table{{width:100%;border-collapse:collapse;font-size:16px}}
th,td{{border:1px solid #444;padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#f0eee4;font-size:13px}}
small{{color:#555}}
p{{font-size:16px;line-height:1.7}}
.foot{{margin-top:26px;font-size:12px;color:#a33;text-align:center}}
</style></head><body><div class="page">
<div class="wm"><span>নমুনা — কাল্পনিক তথ্য · SYNTHETIC</span></div>
<h1>{title}</h1>
<div class="sub">জমিচেক ডেমোর জন্য তৈরি নমুনা ডকুমেন্ট — কোনো সরকারি দলিল নয়</div>
{body}
<div class="foot">এই ছবিটি সম্পূর্ণ কাল্পনিক (সিনথেটিক) তথ্যে তৈরি। This image is synthetic and has no legal value.</div>
</div></body></html>"""


def meta(rows) -> str:
    return '<div class="meta">' + "".join(f"<div><span>{k}</span><b>{v}</b></div>" for k, v in rows) + "</div>"


def location(plot: Plot) -> list:
    m = plot.mouza
    return [("জেলা", esc(m.upazila.district.name_bn)), ("উপজেলা", esc(m.upazila.name_bn)),
            ("মৌজা", esc(m.name_bn)), ("জে.এল. নং", bn(m.jl_no))]


def khatian_html(khatian: Khatian, plot: Plot, owners=None) -> str:
    owners = owners or list(khatian.owners.select_related("person"))
    mutation = Mutation.objects.filter(resulting_khatian=khatian).first()
    title = "নামজারি খতিয়ান" if khatian.survey == "NAMJARI" else f"{khatian.survey} খতিয়ান"
    decimal = plot.area_acre * 100
    total_share = sum(o.share for o in owners)
    owner_rows = "".join(
        f"<tr><td>{bn(i)}</td><td><b>{esc(o.person.name_bn)}</b><br><small>পিতা: {esc(o.person.father_name_bn or '—')}</small></td>"
        f"<td>{esc(share_to_ana(o.share)['bn'])}</td><td>{'মৃত' if o.person.is_deceased else ''}</td></tr>"
        for i, o in enumerate(owners, start=1)
    )
    rows = location(plot) + [("খতিয়ান নং", bn(khatian.khatian_no)), ("রেকর্ড বছর", bn(khatian.record_year))]
    if mutation:
        rows.append(("নামজারি কেস নং", esc(bn(mutation.case_no))))
    return page(title, f"""{meta(rows)}
<h2>মালিকানা অংশ</h2>
<table><tr><th>(১) ক্রমিক নং</th><th>(২) মালিকের নাম ও পিতার নাম</th><th>(৩) অংশ বা হিস্যা</th><th>(৪) মন্তব্য</th></tr>{owner_rows}</table>
<h2>দাগের বিবরণ</h2>
<table><tr><th>(৫) দাগ নং</th><th>(৬) জমির শ্রেণি</th><th>(৭) দাগে মোট জমি</th><th>(৮) অংশ</th><th>(৯) খতিয়ানভুক্ত জমি</th></tr>
<tr><td>{bn(plot.dag_no)}</td><td>{LAND_CLASS_BN.get(plot.land_class, plot.land_class)}</td><td>{area(decimal)} শতাংশ</td>
<td>{esc(share_to_ana(total_share)['bn'])}</td><td>{area(decimal * total_share)} শতাংশ</td></tr></table>""")


def deed_html(deed, plot: Plot) -> str:
    def people(group):
        return "".join(f"<tr><td><b>{esc(p.name_bn)}</b><br><small>পিতা: {esc(p.father_name_bn or '—')}</small></td></tr>"
                       for p in (group.all() if hasattr(group, "all") else group))
    rows = location(plot) + [("দলিল নং", esc(bn(deed.deed_no))),
                             ("রেজিস্ট্রির তারিখ", bn(deed.registration_date.strftime("%d-%m-%Y")))]
    return page("সাফ কবলা দলিল", f"""{meta(rows)}
<p>সাব-রেজিস্ট্রি অফিস: <b>{esc(deed.sub_registry_office)}</b> · মূল্য: <b>{bn(f"{deed.price_bdt:,}")} টাকা</b></p>
<h2>দাতা (বিক্রেতা)</h2><table>{people(deed.sellers)}</table>
<h2>গ্রহীতা (ক্রেতা)</h2><table>{people(deed.buyers)}</table>
<h2>তফসিল (বিক্রীত জমি)</h2>
<table><tr><th>দাগ নং</th><th>জমির শ্রেণি</th><th>বিক্রীত জমি</th></tr>
<tr><td>{bn(plot.dag_no)}</td><td>{LAND_CLASS_BN.get(plot.land_class, plot.land_class)}</td><td>{area(deed.area_acre * 100)} শতাংশ</td></tr></table>""")


def dakhila_html(tax, plot: Plot, owner: Person, paid_upto: int) -> str:
    rows = location(plot) + [("হোল্ডিং নং", esc(bn(tax.holding_no))), ("দাগ নং", bn(plot.dag_no))]
    return page("ভূমি উন্নয়ন কর পরিশোধের রসিদ (দাখিলা)", f"""{meta(rows)}
<p>মালিকের নাম: <b>{esc(owner.name_bn)}</b></p>
<table><tr><th>বিবরণ</th><th>পরিমাণ</th></tr>
<tr><td>যে সাল পর্যন্ত কর পরিশোধিত</td><td><b>{bn(paid_upto)} সাল</b></td></tr>
<tr><td>বকেয়া</td><td>০ টাকা</td></tr></table>""")


def latest_khatian(plot: Plot) -> Khatian:
    return max(plot.khatians.all(), key=lambda k: k.order)


def get_plot(dag: str) -> Plot:
    plot = Plot.objects.filter(mouza__name_en="Rampur", dag_no=dag).select_related("mouza__upazila__district").first()
    if not plot:
        raise CommandError(f"Dag {dag} in Rampur not found. Run `python manage.py seed_demo` first.")
    return plot


def samples():
    """(file name, html) for every sample; names ending in -forged disagree with the records on purpose."""
    for dag in ("101", "118", "125"):
        plot = get_plot(dag)
        yield f"khatian-rampur-{dag}", khatian_html(latest_khatian(plot), plot)

    # An heir shows a BS khatian rewritten in his own name as sole owner.
    p118 = get_plot("118")
    karim = Person.objects.get(name_en="Karim Mia")
    yield "khatian-rampur-118-forged", khatian_html(
        latest_khatian(p118), p118, owners=[SimpleNamespace(person=karim, share=Decimal(1))])

    p101 = get_plot("101")
    yield "deed-rampur-101", deed_html(Deed.objects.get(plot=p101), p101)

    # Rahim backs his claim with a deed that was never registered and a receipt showing no arrears.
    p125 = get_plot("125")
    seller = Person.objects.filter(name_en="Abdul Karim").first()
    rahim = Person.objects.get(name_en="Rahim Uddin")
    fake = SimpleNamespace(
        deed_no="2024-09917", registration_date=Deed.objects.filter(plot=p125).first().registration_date.replace(year=2024),
        sub_registry_office="Savar Sub-Registry Office", price_bdt=780_000, area_acre=p125.area_acre,
        sellers=[seller], buyers=[rahim],
    )
    yield "deed-rampur-125-forged", deed_html(fake, p125)
    yield "dakhila-rampur-125-forged", dakhila_html(TaxRecord.objects.get(plot=p125), p125, rahim, 2026)


class Command(BaseCommand):
    help = "Render synthetic land document sample images (some deliberately forged) for the upload demo."

    def add_arguments(self, parser):
        parser.add_argument("--out", default=str(REPO / "frontend" / "public" / "samples"))

    def handle(self, *args, **opts):
        out = Path(opts["out"])
        out.mkdir(parents=True, exist_ok=True)
        browser = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chromium-browser")
        for name, markup in samples():
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
                tmp.write(markup)
            if not browser:
                shutil.copy(tmp.name, out / f"{name}.html")
                self.stdout.write(f"No Chromium found; wrote {name}.html")
                continue
            subprocess.run(
                [browser, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                 "--window-size=980,760", f"--screenshot={out / f'{name}.png'}", Path(tmp.name).as_uri()],
                check=True, capture_output=True,
            )
            Path(tmp.name).unlink()
            self.stdout.write(self.style.SUCCESS(f"Wrote {name}.png"))
