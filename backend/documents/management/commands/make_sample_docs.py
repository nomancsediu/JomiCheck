"""Render synthetic khatian images for the upload demo.

The images are built from the seeded synthetic records, carry a visible
"synthetic sample" watermark and deliberately avoid any government emblem.
"""
import html
import shutil
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from land.models import Khatian, Mutation, Plot
from land.units import share_to_ana
from verification.engine import LAND_CLASS_BN

SAMPLES = [("Rampur", "101"), ("Rampur", "118"), ("Rampur", "125")]
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
REPO = Path(settings.BASE_DIR).parent


def bn(value) -> str:
    return str(value).translate(BN)


def esc(value) -> str:
    return html.escape(str(value))


def render_html(khatian: Khatian, plot: Plot) -> str:
    mouza = plot.mouza
    owners = list(khatian.owners.select_related("person"))
    mutation = Mutation.objects.filter(resulting_khatian=khatian).first()
    title = "নামজারি খতিয়ান" if khatian.survey == "NAMJARI" else f"{khatian.survey} খতিয়ান"
    decimal = plot.area_acre * 100
    total_share = sum(o.share for o in owners)

    def area(value) -> str:
        return bn(f"{value.quantize(Decimal('0.01')).normalize():f}")

    owner_rows = "".join(
        f"<tr><td>{bn(i)}</td><td><b>{esc(o.person.name_bn)}</b><br><small>পিতা: {esc(o.person.father_name_bn or '—')}</small></td>"
        f"<td>{esc(share_to_ana(o.share)['bn'])}</td><td>{'মৃত' if o.person.is_deceased else ''}</td></tr>"
        for i, o in enumerate(owners, start=1)
    )
    font = REPO / "build" / "fonts" / "NotoSansBengali.ttf"
    font_face = f"@font-face{{font-family:Bn;src:url('{font.as_uri()}')}}" if font.exists() else ""
    case = f"<div><span>নামজারি কেস নং</span><b>{esc(bn(mutation.case_no))}</b></div>" if mutation else ""

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
.foot{{margin-top:26px;font-size:12px;color:#a33;text-align:center}}
</style></head><body><div class="page">
<div class="wm"><span>নমুনা — কাল্পনিক তথ্য · SYNTHETIC</span></div>
<h1>{title}</h1>
<div class="sub">জমিচেক ডেমোর জন্য তৈরি নমুনা ডকুমেন্ট — কোনো সরকারি দলিল নয়</div>
<div class="meta">
<div><span>জেলা</span><b>{esc(mouza.upazila.district.name_bn)}</b></div>
<div><span>উপজেলা</span><b>{esc(mouza.upazila.name_bn)}</b></div>
<div><span>মৌজা</span><b>{esc(mouza.name_bn)}</b></div>
<div><span>জে.এল. নং</span><b>{bn(mouza.jl_no)}</b></div>
<div><span>খতিয়ান নং</span><b>{bn(khatian.khatian_no)}</b></div>
<div><span>রেকর্ড বছর</span><b>{bn(khatian.record_year)}</b></div>
{case}
</div>
<h2>মালিকানা অংশ</h2>
<table><tr><th>(১) ক্রমিক নং</th><th>(২) মালিকের নাম ও পিতার নাম</th><th>(৩) অংশ বা হিস্যা</th><th>(৪) মন্তব্য</th></tr>{owner_rows}</table>
<h2>দাগের বিবরণ</h2>
<table><tr><th>(৫) দাগ নং</th><th>(৬) জমির শ্রেণি</th><th>(৭) দাগে মোট জমি</th><th>(৮) অংশ</th><th>(৯) খতিয়ানভুক্ত জমি</th></tr>
<tr><td>{bn(plot.dag_no)}</td><td>{LAND_CLASS_BN.get(plot.land_class, plot.land_class)}</td><td>{area(decimal)} শতাংশ</td>
<td>{esc(share_to_ana(total_share)['bn'])}</td><td>{area(decimal * total_share)} শতাংশ</td></tr></table>
<div class="foot">এই ছবিটি সম্পূর্ণ কাল্পনিক (সিনথেটিক) তথ্যে তৈরি। This image is synthetic and has no legal value.</div>
</div></body></html>"""


class Command(BaseCommand):
    help = "Render synthetic khatian sample images for the document upload demo."

    def add_arguments(self, parser):
        parser.add_argument("--out", default=str(REPO / "frontend" / "public" / "samples"))

    def handle(self, *args, **opts):
        out = Path(opts["out"])
        out.mkdir(parents=True, exist_ok=True)
        browser = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chromium-browser")
        for mouza_name, dag in SAMPLES:
            plot = Plot.objects.filter(mouza__name_en=mouza_name, dag_no=dag).select_related("mouza__upazila__district").first()
            if not plot:
                raise CommandError(f"Dag {dag} in {mouza_name} not found. Run `python manage.py seed_demo` first.")
            khatian = max(plot.khatians.all(), key=lambda k: k.order)
            name = f"khatian-{mouza_name.lower()}-{dag}"
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
                tmp.write(render_html(khatian, plot))
            if not browser:
                shutil.copy(tmp.name, out / f"{name}.html")
                self.stdout.write(f"No Chromium found; wrote {name}.html")
                continue
            subprocess.run(
                [browser, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                 "--window-size=980,690", f"--screenshot={out / f'{name}.png'}", Path(tmp.name).as_uri()],
                check=True, capture_output=True,
            )
            Path(tmp.name).unlink()
            self.stdout.write(self.style.SUCCESS(f"Wrote {name}.png"))
