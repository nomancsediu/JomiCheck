"""
Synthetic land-record generator.

Every person, plot, khatian, deed and case created here is fictional. Only the
district and upazila names are real public administrative names. The planted
scenarios in DEMO_CASES exercise each verification rule.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from . import models as m

SURVEY_YEAR = {"CS": 1915, "SA": 1962, "RS": 1985, "BS": 2005}

DEMO_CASES = [
    {
        "key": "clean",
        "title_en": "Clean property",
        "title_bn": "ঝুঁকিমুক্ত জমি",
        "summary_en": "Seller is the recorded owner with a complete chain of title.",
        "summary_bn": "বিক্রেতা রেকর্ডভুক্ত মালিক, মালিকানার ধারা সম্পূর্ণ।",
        "mouza": "Rampur", "dag_no": "101", "khatian_no": "1021", "seller_name": "Jamal Hossain", "area_acre": "0.33",
    },
    {
        "key": "rahim_fraud",
        "title_en": "Ownership mismatch and double-selling",
        "title_bn": "মালিকানা অমিল ও একাধিকবার বিক্রি",
        "summary_en": "Seller is not the recorded owner and already sold this plot to someone else.",
        "summary_bn": "বিক্রেতা রেকর্ডভুক্ত মালিক নন এবং জমিটি আগেই অন্যের কাছে বিক্রি করেছেন।",
        "mouza": "Rampur", "dag_no": "125", "khatian_no": "456", "seller_name": "Rahim Uddin", "area_acre": "0.30",
    },
    {
        "key": "inheritance_oversell",
        "title_en": "Heir selling more than his share",
        "title_bn": "ওয়ারিশ নিজের অংশের বেশি বিক্রি করছেন",
        "summary_en": "A son of the deceased owner sells 0.40 acre, but his Faraiz share is 0.35 acre.",
        "summary_bn": "মৃত মালিকের এক ছেলে ০.৪০ একর বিক্রি করছেন, কিন্তু ফারায়েজ অনুযায়ী তাঁর অংশ ০.৩৫ একর।",
        "mouza": "Rampur", "dag_no": "118", "khatian_no": "300", "seller_name": "Karim Mia", "area_acre": "0.40",
    },
    {
        "key": "mutation_missing",
        "title_en": "Bought by deed, mutation rejected",
        "title_bn": "দলিলে কেনা, নামজারি বাতিল",
        "summary_en": "Seller bought by deed at a very low price; mutation was rejected.",
        "summary_bn": "বিক্রেতা খুব কম দামে দলিলে কিনেছেন; নামজারি বাতিল হয়েছে।",
        "mouza": "Rampur", "dag_no": "132", "khatian_no": "470", "seller_name": "Shafiq Ahmed", "area_acre": "0.25",
    },
    {
        "key": "khas_land",
        "title_en": "Khas (government) land",
        "title_bn": "খাস (সরকারি) জমি",
        "summary_en": "Government khas land offered for sale by a private person.",
        "summary_bn": "সরকারি খাস জমি একজন ব্যক্তি বিক্রি করতে চাইছেন।",
        "mouza": "Charabag", "dag_no": "140", "khatian_no": "1", "seller_name": "Bashir Ahmed", "area_acre": "0.50",
    },
    {
        "key": "acquisition",
        "title_en": "Under government acquisition",
        "title_bn": "সরকারি অধিগ্রহণাধীন",
        "summary_en": "Recorded owner is selling, but an acquisition notice is active.",
        "summary_bn": "রেকর্ডভুক্ত মালিক বিক্রি করছেন, কিন্তু অধিগ্রহণের নোটিশ চলমান।",
        "mouza": "Charabag", "dag_no": "150", "khatian_no": "520", "seller_name": "Liton Das", "area_acre": "0.40",
    },
    {
        "key": "litigation",
        "title_en": "Pending suit with injunction",
        "title_bn": "চলমান মামলা ও নিষেধাজ্ঞা",
        "summary_en": "A title suit is pending and the court has restrained transfer.",
        "summary_bn": "স্বত্ব মামলা চলমান এবং আদালত হস্তান্তরে নিষেধাজ্ঞা দিয়েছেন।",
        "mouza": "Charabag", "dag_no": "160", "khatian_no": "530", "seller_name": "Habib Ullah", "area_acre": "0.30",
    },
    {
        "key": "mortgage",
        "title_en": "Mortgaged to a bank",
        "title_bn": "ব্যাংকে বন্ধক",
        "summary_en": "The plot is mortgaged against an active bank loan.",
        "summary_bn": "জমিটি চলমান ব্যাংক ঋণের বিপরীতে বন্ধক রাখা।",
        "mouza": "Charabag", "dag_no": "170", "khatian_no": "540", "seller_name": "Sumon Ali", "area_acre": "0.20",
    },
    {
        "key": "revoked_poa",
        "title_en": "Sale through revoked power of attorney",
        "title_bn": "বাতিল আমমোক্তারনামায় বিক্রি",
        "summary_en": "Attorney of an overseas owner sells using a revoked power of attorney.",
        "summary_bn": "প্রবাসী মালিকের আমমোক্তার বাতিল হওয়া আমমোক্তারনামা দিয়ে বিক্রি করছেন।",
        "mouza": "Charabag", "dag_no": "180", "khatian_no": "550", "seller_name": "Faruk Ahmed", "area_acre": "0.35",
    },
    {
        "key": "bainanama",
        "title_en": "Prior agreement for sale",
        "title_bn": "আগের বায়নানামা",
        "summary_en": "Co-owner already signed a registered bainanama with another buyer.",
        "summary_bn": "শরিক মালিক আগেই অন্য ক্রেতার সাথে নিবন্ধিত বায়নানামা করেছেন।",
        "mouza": "Notunhat", "dag_no": "190", "khatian_no": "610", "seller_name": "Delwar Hossain", "area_acre": "0.20",
    },
    {
        "key": "survey_conflict",
        "title_en": "Break in survey records",
        "title_bn": "জরিপ রেকর্ডে অসংগতি",
        "summary_en": "Owner changed between SA and RS survey with no deed or inheritance link.",
        "summary_bn": "এসএ ও আরএস জরিপের মধ্যে কোনো দলিল বা উত্তরাধিকার ছাড়াই মালিক বদলেছে।",
        "mouza": "Notunhat", "dag_no": "205", "khatian_no": "620", "seller_name": "Rafiq Mondol", "area_acre": "0.60",
    },
    {
        "key": "rapid_transfers",
        "title_en": "Rapid low-price transfers",
        "title_bn": "দ্রুত ও কম দামে হাতবদল",
        "summary_en": "Three sales in six months, all far below the mouza rate.",
        "summary_bn": "ছয় মাসে তিনবার বিক্রি, সবগুলো মৌজা রেটের অনেক নিচে।",
        "mouza": "Notunhat", "dag_no": "215", "khatian_no": "631", "seller_name": "Imran Hossain", "area_acre": "0.15",
    },
    {
        "key": "minor_heir",
        "title_en": "Mother selling a minor heir's land",
        "title_bn": "নাবালক ওয়ারিশের জমি মা বিক্রি করছেন",
        "summary_en": "Widow sells the whole plot although most of it belongs to her minor son.",
        "summary_bn": "বিধবা পুরো জমি বিক্রি করছেন, যদিও বেশিরভাগ অংশ তাঁর নাবালক ছেলের।",
        "mouza": "Shantipur", "dag_no": "225", "khatian_no": "710", "seller_name": "Nasima Begum", "area_acre": "0.50",
    },
    {
        "key": "ml_broker",
        "title_en": "Quick resale by a land broker (caught by ML)",
        "title_bn": "দালালের দ্রুত পুনঃবিক্রি (মেশিন লার্নিং ধরেছে)",
        "summary_en": "Seller is the recorded owner and no rule is broken, but he bought months ago and sold three other dags this year.",
        "summary_bn": "বিক্রেতা রেকর্ডভুক্ত মালিক, কোনো নিয়ম ভাঙেনি; কিন্তু কয়েক মাস আগে কিনেছেন এবং এ বছর আরও তিনটি দাগ বিক্রি করেছেন।",
        "mouza": "Charabag", "dag_no": "235", "khatian_no": "845", "seller_name": "Selim Reza", "area_acre": "0.25",
    },
]

FIRST_NAMES = [
    ("Abul", "আবুল"), ("Babul", "বাবুল"), ("Nasir", "নাসির"), ("Ruhul", "রুহুল"), ("Shahid", "শহিদ"),
    ("Mamun", "মামুন"), ("Tariq", "তারিক"), ("Rashed", "রাশেদ"), ("Masud", "মাসুদ"), ("Kabir", "কবির"),
    ("Jasim", "জসিম"), ("Alamgir", "আলমগীর"),
]
LAST_NAMES = [
    ("Hossain", "হোসেন"), ("Ahmed", "আহমেদ"), ("Mia", "মিয়া"), ("Sarker", "সরকার"),
    ("Uddin", "উদ্দিন"), ("Khan", "খান"), ("Mollah", "মোল্লা"), ("Sheikh", "শেখ"),
]


class Seeder:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self._nid = 0
        self._deed = 0
        self._case = 0

    # --- primitives -------------------------------------------------------
    def person(self, name_en, name_bn, gender="M", religion="muslim", **kw):
        self._nid += 1
        return m.Person.objects.create(
            name_en=name_en, name_bn=name_bn, gender=gender, religion=religion,
            nid=f"{self._nid:010d}", **kw,
        )

    def heirs(self, deceased, *pairs):
        for heir, relation in pairs:
            m.HeirLink.objects.create(deceased=deceased, heir=heir, relation=relation)
            if not heir.father_name_en and deceased.gender == "M" and relation in ("son", "daughter"):
                heir.father_name_en, heir.father_name_bn = deceased.name_en, deceased.name_bn
                heir.save(update_fields=["father_name_en", "father_name_bn"])

    def plot(self, mouza, dag, area, rate, land_class="agricultural"):
        return m.Plot.objects.create(
            mouza=mouza, dag_no=str(dag), area_acre=Decimal(area),
            mouza_rate_per_acre=rate, land_class=land_class,
        )

    def khatian(self, mouza, no, survey, plots, owners, year=None):
        k = m.Khatian.objects.create(
            mouza=mouza, khatian_no=str(no), survey=survey, record_year=year or SURVEY_YEAR[survey],
        )
        k.plots.set(plots)
        for person, share in owners:
            m.KhatianOwner.objects.create(khatian=k, person=person, share=Decimal(share))
        return k

    def deed(self, plot, when, area, price, sellers, buyers, office, deed_type="sale"):
        self._deed += 1
        d = m.Deed.objects.create(
            deed_no=f"{when.year}-{self._deed:05d}", deed_type=deed_type, registration_date=when,
            sub_registry_office=office, plot=plot, area_acre=Decimal(area), price_bdt=price,
        )
        d.sellers.set(sellers)
        d.buyers.set(buyers)
        return d

    def mutation(self, plot, owner, when, status, deed=None, khatian=None):
        self._case += 1
        return m.Mutation.objects.create(
            case_no=f"NJ-{when.year}-{self._case:04d}", plot=plot, new_owner=owner, deed=deed,
            resulting_khatian=khatian, application_date=when, status=status,
        )

    def tax(self, plot, paid_upto=2026, arrears=0):
        return m.TaxRecord.objects.create(
            plot=plot, holding_no=f"H-{plot.mouza.jl_no}-{plot.dag_no}", paid_upto_year=paid_upto,
            arrears_bdt=arrears,
        )

    def family_lineage(self, mouza, plot, father, child, sa_no, rs_no, bs_no, bs_owners=None):
        """SA and RS in the father's name, BS in the child's name after inheritance."""
        self.khatian(mouza, sa_no, "SA", [plot], [(father, 1)])
        self.khatian(mouza, rs_no, "RS", [plot], [(father, 1)])
        return self.khatian(mouza, bs_no, "BS", [plot], bs_owners or [(child, 1)])

    def random_name(self):
        f, l = self.rng.choice(FIRST_NAMES), self.rng.choice(LAST_NAMES)
        return f"{f[0]} {l[0]}", f"{f[1]} {l[1]}"


def clear():
    for model in [
        m.PurchaseIntent, m.TaxRecord, m.Mortgage, m.LegalStatus, m.PowerOfAttorney, m.Mutation,
        m.Bainanama, m.Deed, m.KhatianOwner, m.Khatian, m.Plot, m.HeirLink, m.Person,
        m.Mouza, m.Upazila, m.District,
    ]:
        model.objects.all().delete()


@transaction.atomic
def seed(random_seed: int = 42) -> dict:
    clear()
    s = Seeder(random.Random(random_seed))

    dhaka = m.District.objects.create(name_en="Dhaka", name_bn="ঢাকা")
    gazipur = m.District.objects.create(name_en="Gazipur", name_bn="গাজীপুর")
    savar = m.Upazila.objects.create(district=dhaka, name_en="Savar", name_bn="সাভার")
    keraniganj = m.Upazila.objects.create(district=dhaka, name_en="Keraniganj", name_bn="কেরানীগঞ্জ")
    kaliakair = m.Upazila.objects.create(district=gazipur, name_en="Kaliakair", name_bn="কালিয়াকৈর")

    rampur = m.Mouza.objects.create(upazila=savar, name_en="Rampur", name_bn="রামপুর", jl_no=101)
    charabag = m.Mouza.objects.create(upazila=savar, name_en="Charabag", name_bn="চরাবাগ", jl_no=102)
    notunhat = m.Mouza.objects.create(upazila=keraniganj, name_en="Notunhat", name_bn="নতুনহাট", jl_no=55)
    shantipur = m.Mouza.objects.create(upazila=kaliakair, name_en="Shantipur", name_bn="শান্তিপুর", jl_no=77)

    SAVAR_SR = "Savar Sub-Registry Office"
    KERANI_SR = "Keraniganj Sub-Registry Office"
    KALIA_SR = "Kaliakair Sub-Registry Office"

    # 1. Clean property ------------------------------------------------------
    wahab = s.person("Abdul Wahab", "আব্দুল ওয়াহাব", is_deceased=True, date_of_death=date(1990, 3, 4))
    nurul = s.person("Nurul Islam", "নুরুল ইসলাম")
    jamal = s.person("Jamal Hossain", "জামাল হোসেন", father_name_en="Kashem Hossain", father_name_bn="কাশেম হোসেন")
    s.heirs(wahab, (nurul, "son"))
    p101 = s.plot(rampur, 101, "0.33", 2_600_000, "homestead")
    s.khatian(rampur, 45, "SA", [p101], [(wahab, 1)])
    s.khatian(rampur, 88, "RS", [p101], [(wahab, 1)])
    s.khatian(rampur, 210, "BS", [p101], [(nurul, 1)])
    d = s.deed(p101, date(2015, 6, 14), "0.33", 880_000, [nurul], [jamal], SAVAR_SR)
    k = s.khatian(rampur, 1021, "NAMJARI", [p101], [(jamal, 1)], year=2016)
    s.mutation(p101, jamal, date(2015, 9, 1), "approved", deed=d, khatian=k)
    s.tax(p101, paid_upto=2025, arrears=1_200)

    # 2. Rahim: ownership mismatch + double-selling --------------------------
    hamid = s.person("Abdul Hamid", "আব্দুল হামিদ", is_deceased=True, date_of_death=date(1995, 8, 20))
    karim_owner = s.person("Abdul Karim", "আব্দুল করিম")
    s.heirs(hamid, (karim_owner, "son"))
    rahim = s.person("Rahim Uddin", "রহিম উদ্দিন", father_name_en="Mofazzal Uddin", father_name_bn="মোফাজ্জল উদ্দিন")
    selim = s.person("Selim Reza", "সেলিম রেজা")
    p125 = s.plot(rampur, 125, "0.30", 2_600_000, "homestead")
    s.family_lineage(rampur, p125, hamid, karim_owner, 52, 95, 456)
    s.deed(p125, date(2025, 11, 10), "0.30", 750_000, [rahim], [selim], SAVAR_SR)
    s.tax(p125, paid_upto=2024, arrears=2_400)

    # 3. Heir over-selling ---------------------------------------------------
    kalu = s.person("Haji Kalu Mia", "হাজী কালু মিয়া", is_deceased=True, date_of_death=date(1978, 1, 12))
    majid = s.person("Abdul Majid", "আব্দুল মজিদ", is_deceased=True, date_of_death=date(2022, 5, 9))
    s.heirs(kalu, (majid, "son"))
    fatema = s.person("Fatema Begum", "ফাতেমা বেগম", gender="F")
    karim = s.person("Karim Mia", "করিম মিয়া")
    hasan = s.person("Hasan Mia", "হাসান মিয়া")
    rokeya = s.person("Rokeya Begum", "রোকেয়া বেগম", gender="F")
    s.heirs(majid, (fatema, "wife"), (karim, "son"), (hasan, "son"), (rokeya, "daughter"))
    p118 = s.plot(rampur, 118, "1.00", 1_800_000)
    s.family_lineage(rampur, p118, kalu, majid, 47, 101, 300)
    s.tax(p118)

    # 4. Bought by deed, mutation rejected, under-priced ---------------------
    jalal = s.person("Jalal Uddin", "জালাল উদ্দিন", is_deceased=True, date_of_death=date(2000, 2, 2))
    monir = s.person("Monir Hossain", "মনির হোসেন")
    s.heirs(jalal, (monir, "son"))
    shafiq = s.person("Shafiq Ahmed", "শফিক আহমেদ")
    p132 = s.plot(rampur, 132, "0.25", 2_600_000, "homestead")
    s.family_lineage(rampur, p132, jalal, monir, 53, 110, 470)
    d = s.deed(p132, date(2023, 4, 18), "0.25", 250_000, [monir], [shafiq], SAVAR_SR)
    s.mutation(p132, shafiq, date(2023, 7, 3), "rejected", deed=d)
    s.tax(p132, paid_upto=2023, arrears=3_000)

    # 5. Khas land -----------------------------------------------------------
    govt = s.person("Government of Bangladesh (Khas)", "বাংলাদেশ সরকার (খাস)", is_government=True)
    s.person("Bashir Ahmed", "বশির আহমেদ")  # exists in the registry but holds no right in this plot
    p140 = s.plot(charabag, 140, "0.50", 2_000_000)
    s.khatian(charabag, 1, "SA", [p140], [(govt, 1)])
    s.khatian(charabag, 1, "BS", [p140], [(govt, 1)])
    m.LegalStatus.objects.create(
        plot=p140, status_type="khas", reference_no="Khas Khatian 1 (BS)",
        description="Recorded as government khas land", since=date(2005, 1, 1),
    )
    s.tax(p140)

    # 6. Acquisition ---------------------------------------------------------
    shyamal = s.person("Shyamal Das", "শ্যামল দাস", religion="hindu", is_deceased=True, date_of_death=date(2001, 6, 1))
    liton = s.person("Liton Das", "লিটন দাস", religion="hindu")
    s.heirs(shyamal, (liton, "son"))
    p150 = s.plot(charabag, 150, "0.40", 2_000_000)
    s.family_lineage(charabag, p150, shyamal, liton, 61, 130, 520)
    m.LegalStatus.objects.create(
        plot=p150, status_type="acquisition", reference_no="LA Case 07/2025-26",
        description="Road widening project — notice under Section 4 served", since=date(2025, 12, 1),
    )
    s.tax(p150)

    # 7. Litigation + injunction --------------------------------------------
    sultan = s.person("Sultan Ahmed", "সুলতান আহমেদ", is_deceased=True, date_of_death=date(1998, 4, 4))
    habib = s.person("Habib Ullah", "হাবিব উল্লাহ")
    s.heirs(sultan, (habib, "son"))
    p160 = s.plot(charabag, 160, "0.30", 2_000_000)
    s.family_lineage(charabag, p160, sultan, habib, 62, 131, 530)
    m.LegalStatus.objects.create(
        plot=p160, status_type="civil_suit", reference_no="Title Suit 214/2024",
        description="Title suit pending before Joint District Judge Court, Dhaka", since=date(2024, 8, 11),
    )
    m.LegalStatus.objects.create(
        plot=p160, status_type="injunction", reference_no="Order No. 5 in TS 214/2024",
        description="Temporary injunction restraining transfer of the suit land", since=date(2024, 9, 2),
    )
    s.tax(p160)

    # 8. Mortgage ------------------------------------------------------------
    aziz = s.person("Aziz Ali", "আজিজ আলী", is_deceased=True, date_of_death=date(2010, 10, 10))
    sumon = s.person("Sumon Ali", "সুমন আলী")
    s.heirs(aziz, (sumon, "son"))
    p170 = s.plot(charabag, 170, "0.20", 2_000_000, "homestead")
    s.family_lineage(charabag, p170, aziz, sumon, 63, 132, 540)
    m.Mortgage.objects.create(
        plot=p170, mortgagor=sumon, lender="Synthetic Commercial Bank Ltd.", amount_bdt=1_500_000,
        registered_on=date(2024, 2, 20),
    )
    s.tax(p170, paid_upto=2024, arrears=1_800)

    # 9. Revoked power of attorney -------------------------------------------
    mokbul = s.person("Mokbul Hossain", "মকবুল হোসেন", is_deceased=True, date_of_death=date(2005, 7, 7))
    anwar = s.person("Anwar Hossain", "আনোয়ার হোসেন")
    s.heirs(mokbul, (anwar, "son"))
    faruk = s.person("Faruk Ahmed", "ফারুক আহমেদ")
    p180 = s.plot(charabag, 180, "0.35", 2_000_000)
    s.khatian(charabag, 64, "SA", [p180], [(mokbul, 1)])
    s.khatian(charabag, 133, "RS", [p180], [(mokbul, 1)])
    s.khatian(charabag, 550, "BS", [p180], [(anwar, 1)], year=2008)
    m.PowerOfAttorney.objects.create(
        poa_no="POA-2022-0180", principal=anwar, attorney=faruk, plot=p180, scope="sale",
        is_registered=True, is_revoked=True, executed_on=date(2022, 1, 15),
    )
    s.tax(p180)

    # 10. Prior bainanama by a co-owner --------------------------------------
    rustam = s.person("Rustam Ali", "রুস্তম আলী", is_deceased=True, date_of_death=date(1999, 9, 9))
    delwar = s.person("Delwar Hossain", "দেলোয়ার হোসেন")
    jahangir = s.person("Jahangir Hossain", "জাহাঙ্গীর হোসেন")
    s.heirs(rustam, (delwar, "son"), (jahangir, "son"))
    kamal = s.person("Kamal Uddin", "কামাল উদ্দিন")
    p190 = s.plot(notunhat, 190, "0.50", 2_200_000)
    s.family_lineage(notunhat, p190, rustam, None, 70, 138, 610, bs_owners=[(delwar, "0.5"), (jahangir, "0.5")])
    m.Bainanama.objects.create(
        agreement_no="BN-2026-0190", plot=p190, seller=delwar, buyer=kamal, area_acre=Decimal("0.20"),
        agreement_date=date(2026, 3, 2), is_registered=True,
    )
    s.tax(p190, paid_upto=2025, arrears=900)

    # 11. Survey conflict ----------------------------------------------------
    moslem = s.person("Moslem Uddin", "মোসলেম উদ্দিন", is_deceased=True, date_of_death=date(1980, 1, 1))
    rafiq = s.person("Rafiq Mondol", "রফিক মন্ডল")
    p205 = s.plot(notunhat, 205, "0.60", 2_200_000)
    s.khatian(notunhat, 72, "SA", [p205], [(moslem, 1)])
    s.khatian(notunhat, 140, "RS", [p205], [(rafiq, 1)])
    s.khatian(notunhat, 620, "BS", [p205], [(rafiq, 1)])
    s.tax(p205, paid_upto=2024, arrears=1_500)

    # 12. Rapid low-price transfers ------------------------------------------
    taher = s.person("Abu Taher", "আবু তাহের")
    mizan = s.person("Mizanur Rahman", "মিজানুর রহমান")
    sohel = s.person("Sohel Rana", "সোহেল রানা")
    imran = s.person("Imran Hossain", "ইমরান হোসেন")
    p215 = s.plot(notunhat, 215, "0.15", 4_000_000, "commercial")
    s.khatian(notunhat, 75, "SA", [p215], [(taher, 1)])
    s.khatian(notunhat, 142, "RS", [p215], [(taher, 1)])
    s.khatian(notunhat, 630, "BS", [p215], [(taher, 1)])
    d1 = s.deed(p215, date(2025, 12, 1), "0.15", 200_000, [taher], [mizan], KERANI_SR)
    d2 = s.deed(p215, date(2026, 2, 15), "0.15", 220_000, [mizan], [sohel], KERANI_SR)
    d3 = s.deed(p215, date(2026, 5, 20), "0.15", 250_000, [sohel], [imran], KERANI_SR)
    s.mutation(p215, mizan, date(2025, 12, 20), "approved", deed=d1)
    s.mutation(p215, sohel, date(2026, 3, 1), "approved", deed=d2)
    k = s.khatian(notunhat, 631, "NAMJARI", [p215], [(imran, 1)], year=2026)
    s.mutation(p215, imran, date(2026, 6, 2), "approved", deed=d3, khatian=k)
    s.tax(p215)

    # 13. Widow selling minor heir's land ------------------------------------
    mofiz = s.person("Mofiz Uddin", "মফিজ উদ্দিন", is_deceased=True, date_of_death=date(2023, 11, 30))
    nasima = s.person("Nasima Begum", "নাসিমা বেগম", gender="F")
    tanvir = s.person("Tanvir Uddin", "তানভীর উদ্দিন", is_minor=True)
    s.heirs(mofiz, (nasima, "wife"), (tanvir, "son"))
    p225 = s.plot(shantipur, 225, "0.50", 1_200_000)
    s.khatian(shantipur, 80, "SA", [p225], [(mofiz, 1)], year=1962)
    s.khatian(shantipur, 150, "RS", [p225], [(mofiz, 1)])
    s.khatian(shantipur, 710, "BS", [p225], [(mofiz, 1)])
    s.tax(p225)

    # 14. Land broker reselling quickly (only the anomaly model notices) -------
    # Dates are relative to today so the pattern stays "recent" whenever the demo is seeded.
    today = date.today()
    selim = s.person("Selim Reza", "সেলিম রেজা", father_name_en="Abdul Wahab", father_name_bn="আব্দুল ওয়াহাব")
    rob = s.person("Abdur Rob", "আব্দুর রব", father_name_en="Nur Mohammad", father_name_bn="নূর মোহাম্মদ")
    p235 = s.plot(charabag, 235, "0.25", 2_000_000, "homestead")
    s.khatian(charabag, 96, "SA", [p235], [(rob, 1)])
    s.khatian(charabag, 196, "RS", [p235], [(rob, 1)])
    s.khatian(charabag, 545, "BS", [p235], [(rob, 1)])
    d = s.deed(p235, today - timedelta(days=140), "0.25", 420_000, [rob], [selim], SAVAR_SR)
    k = s.khatian(charabag, 845, "NAMJARI", [p235], [(selim, 1)], year=today.year)
    s.mutation(p235, selim, today - timedelta(days=125), "approved", deed=d, khatian=k)
    s.tax(p235)
    for i, (dag, bought_ago, sold_ago) in enumerate([(236, 330, 250), (237, 290, 190), (238, 240, 100)]):
        en, bn = s.random_name()
        owner = s.person(en, bn)
        en, bn = s.random_name()
        buyer = s.person(en, bn)
        plot = s.plot(charabag, dag, "0.20", 2_000_000, "homestead")
        s.khatian(charabag, 97 + i, "SA", [plot], [(owner, 1)])
        s.khatian(charabag, 197 + i, "RS", [plot], [(owner, 1)])
        s.khatian(charabag, 546 + i, "BS", [plot], [(owner, 1)])
        s.deed(plot, today - timedelta(days=bought_ago), "0.20", 330_000, [owner], [selim], SAVAR_SR)
        s.deed(plot, today - timedelta(days=sold_ago), "0.20", 360_000, [selim], [buyer], SAVAR_SR)
        s.tax(plot)

    # Background: ordinary clean plots ---------------------------------------
    offices = {rampur: SAVAR_SR, charabag: SAVAR_SR, notunhat: KERANI_SR, shantipur: KALIA_SR}
    background = 0
    for mouza in (rampur, charabag, notunhat, shantipur):
        for i in range(8):
            dag = 300 + i * 7
            area = Decimal(s.rng.choice(["0.10", "0.20", "0.25", "0.33", "0.50", "0.66", "1.00"]))
            rate = {rampur: 2_600_000, charabag: 2_000_000, notunhat: 2_200_000, shantipur: 1_200_000}[mouza]
            plot = s.plot(mouza, dag, area, rate)
            en, bn = s.random_name()
            father = s.person(en, bn, is_deceased=True, date_of_death=date(s.rng.randint(1985, 2015), 1, 1))
            en, bn = s.random_name()
            child = s.person(en, bn)
            s.heirs(father, (child, "son"))
            base = 900 + i * 10
            s.family_lineage(mouza, plot, father, child, base, base + 1, base + 2)
            arrears = s.rng.choice([0, 0, 0, 600, 1_100])
            s.tax(plot, paid_upto=2026 if arrears == 0 else 2025, arrears=arrears)
            background += 1

    return {
        "districts": m.District.objects.count(),
        "mouzas": m.Mouza.objects.count(),
        "plots": m.Plot.objects.count(),
        "people": m.Person.objects.count(),
        "khatians": m.Khatian.objects.count(),
        "deeds": m.Deed.objects.count(),
        "demo_cases": len(DEMO_CASES),
        "background_plots": background,
    }
