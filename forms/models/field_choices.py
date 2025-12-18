from django.db import models


class ProfessionChoices(models.TextChoices):
    TEACHER = "শিক্ষক", "শিক্ষক"
    DOCTOR = "ডাক্তার", "ডাক্তার"
    ENGINEER = "ইঞ্জিনিয়ার", "ইঞ্জিনিয়ার"
    LAWYER = "আইনজীবী", "আইনজীবী"
    FARMER = "কৃষক", "কৃষক"
    BUSINESSMAN = "ব্যবসায়ী", "ব্যবসায়ী"
    EMPLOYEE = "চাকরিজীবী", "চাকরিজীবী"
    FREELANCER = "ফ্রিল্যান্সার", "ফ্রিল্যান্সার"
    STUDENT = "ছাত্র", "ছাত্র"
    PHYSICIAN = "চিকিৎসক", "চিকিৎসক"
    OTHER = "অন্যান্য", "অন্যান্য"


class InterestedPersonChoices(models.TextChoices):
    SELF = "নিজে আসতে চায়", "নিজে আসতে চায়"
    SEND_OTHER = "অন্য কাউকে পাঠাতে চায়", "অন্য কাউকে পাঠাতে চায়"


class CourseSourceChoices(models.TextChoices):
    FACEBOOK_POST = "ফেসবুক পোস্টের মাধ্যমে", "ফেসবুক পোস্টের মাধ্যমে"
    SPEECH = "বক্তব্যের মাধ্যমে", "বক্তব্যের মাধ্যমে"
    ACQUAINTANCE = "পরিচিত ব্যক্তির মাধ্যমে", "পরিচিত ব্যক্তির মাধ্যমে"
    OTHER = "অন্যান্য", "অন্যান্য"


class DistrictChoices(models.TextChoices):
    COX_BAZAR = "কক্সবাজার", "কক্সবাজার"
    KURIGRAM = "কুড়িগ্রাম", "কুড়িগ্রাম"
    KUSHTIA = "কুষ্টিয়া", "কুষ্টিয়া"
    KISHOREGANJ = "কিশোরগঞ্জ", "কিশোরগঞ্জ"
    KHAGRACHARI = "খাগড়াছড়ি", "খাগড়াছড়ি"
    KHULNA = "খুলনা", "খুলনা"
    GAIBANDHA = "গাইবান্ধা", "গাইবান্ধা"
    GAZIPUR = "গাজীপুর", "গাজীপুর"
    GOPALGANJ = "গোপালগঞ্জ", "গোপালগঞ্জ"
    CHATTOGRAM = "চট্টগ্রাম", "চট্টগ্রাম"
    CHANDPUR = "চাঁদপুর", "চাঁদপুর"
    CHAPAINAWABGANJ = "চাঁপাইনবাবগঞ্জ", "চাঁপাইনবাবগঞ্জ"
    CHUADANGA = "চুয়াডাঙ্গা", "চুয়াডাঙ্গা"
    JHALAKATHI = "ঝালকাঠি", "ঝালকাঠি"
    JHENAIDAH = "ঝিনাইদহ", "ঝিনাইদহ"
    TANGAIL = "টাঙ্গাইল", "টাঙ্গাইল"
    THAKURGAON = "ঠাকুরগাঁও", "ঠাকুরগাঁও"
    DINAJPUR = "দিনাজপুর", "দিনাজপুর"
    DHAKA = "ঢাকা", "ঢাকা"
    NAOGAON = "নওগাঁ", "নওগাঁ"
    NATORE = "নাটোর", "নাটোর"
    NARSINGDI = "নরসিংদী", "নরসিংদী"
    NARAYANGANJ = "নারায়ণগঞ্জ", "নারায়ণগঞ্জ"
    NILPHAMARI = "নীলফামারী", "নীলফামারী"
    NORAIL = "নড়াইল", "নড়াইল"
    PABNA = "পাবনা", "পাবনা"
    PATUAKHALI = "পটুয়াখালী", "পটুয়াখালী"
    PIROJPUR = "পিরোজপুর", "পিরোজপুর"
    PANCHAGARH = "পঞ্চগড়", "পঞ্চগড়"
    FENI = "ফেনী", "ফেনী"
    FARIDPUR = "ফরিদপুর", "ফরিদপুর"
    BAGERHAT = "বাগেরহাট", "বাগেরহাট"
    BARGUNA = "বরগুনা", "বরগুনা"
    BARISHAL = "বরিশাল", "বরিশাল"
    BOGRA = "বগুড়া", "বগুড়া"
    BANDARBAN = "বান্দরবান", "বান্দরবান"
    BRAHMANBARIA = "ব্রাহ্মণবাড়িয়া", "ব্রাহ্মণবাড়িয়া"
    BHOLA = "ভোলা", "ভোলা"
    MAGURA = "মাগুরা", "মাগুরা"
    MADARIPUR = "মাদারীপুর", "মাদারীপুর"
    MANIKGANJ = "মানিকগঞ্জ", "মানিকগঞ্জ"
    MYMENSINGH = "ময়মনসিংহ", "ময়মনসিংহ"
    MOULVIBAZAR = "মৌলভীবাজার", "মৌলভীবাজার"
    MEHERPUR = "মেহেরপুর", "মেহেরপুর"
    MUNSHIGANJ = "মুন্সিগঞ্জ", "মুন্সিগঞ্জ"
    JASHORE = "যশোর", "যশোর"
    JOYPURHAT = "জয়পুরহাট", "জয়পুরহাট"
    JAMALPUR = "জামালপুর", "জামালপুর"
    RAJBARI = "রাজবাড়ী", "রাজবাড়ী"
    RAJSHAHI = "রাজশাহী", "রাজশাহী"
    RANGAMATI = "রাঙামাটি", "রাঙামাটি"
    LALMONIRHAT = "লালমনিরহাট", "লালমনিরহাট"
    LAKSHMIPUR = "লক্ষ্মীপুর", "লক্ষ্মীপুর"
    SHERPUR = "শেরপুর", "শেরপুর"
    SHARIATPUR = "শরীয়তপুর", "শরীয়তপুর"
    SUNAMGANJ = "সুনামগঞ্জ", "সুনামগঞ্জ"
    SIRAJGANJ = "সিরাজগঞ্জ", "সিরাজগঞ্জ"
    SYLHET = "সিলেট", "সিলেট"
    HABIGANJ = "হবিগঞ্জ", "হবিগঞ্জ"




class ProgramTypeChoices(models.TextChoices):
    MADRASA_DEVELOPMENT = "মাদ্রাসা উন্নয়ন", "মাদ্রাসা উন্নয়ন"
    MOSQUE_DEVELOPMENT = "মসজিদ উন্নয়ন", "মসজিদ উন্নয়ন"
    GRAVEYARD_DEVELOPMENT = "গোরস্থান উন্নয়ন", "গোরস্থান উন্নয়ন"
    EIDGAH_DEVELOPMENT = "ইদগাহ উন্নয়ন", "ইদগাহ উন্নয়ন"
    DAWAH_WORK = "দাওয়াতি কাজে", "দাওয়াতি কাজে"
    MAKTAB_DEVELOPMENT = "মক্তব উন্নয়ন", "মক্তব উন্নয়ন"


class ProgramTimeChoices(models.TextChoices):
    AFTER_ZUHR = "বাদ যোহর", "বাদ যোহর"
    AFTER_ASR = "বাদ আসর", "বাদ আসর"
    AFTER_MAGHRIB = "বাদ মাগরিব", "বাদ মাগরিব"
    AFTER_ISHA = "বাদ এশা", "বাদ এশা"
    NIGHT = "রাত", "রাত"


class YesNoChoices(models.TextChoices):
    YES = "হ্যাঁ", "হ্যাঁ"
    NO = "না", "না"


class ProgramFundCollectionChoices(models.TextChoices):
    FROM_AREA = "এলাকা থেকে", "এলাকা থেকে"
    FROM_PROGRAM = "প্রোগ্রাম থেকে", "প্রোগ্রাম থেকে"
    FROM_INSTITUTION = "প্রতিষ্ঠান থেকে", "প্রতিষ্ঠান থেকে"
    SPECIAL_PERSON = "বিশেষ ব্যক্তি", "বিশেষ ব্যক্তি"


class SpeakerChoices(models.TextChoices):
    ABDUR_RAZZAK = "আব্দুর রাজ্জাক বিন ইউসুফ", "আব্দুর রাজ্জাক বিন ইউসুফ"
    ABDULLAH_BIN_ABDUR_RAZZAK = "আব্দুল্লাহ বিন আব্দুর রাজ্জাক", "আব্দুল্লাহ বিন আব্দুর রাজ্জাক"
    ABDUR_RAHMAN_BIN_ABDUR_RAZZAK = "আব্দুর রহমান বিন আব্দুর রাজ্জাক", "আব্দুর রহমান বিন আব্দুর রাজ্জাক"
    ABDUR_RAHIM_BIN_ABDUR_RAZZAK = "আব্দুর রহিম বিন আব্দুর রাজ্জাক", "আব্দুর রহিম বিন আব্দুর রাজ্জাক"
    ABDUL_ALIM_MADANI = "আব্দুল আলিম মাদানি", "আব্দুল আলিম মাদানি"
    MAHBUBUR_RAHMAN_MADANI = "মাহবুবুর রহমান মাদানি", "মাহবুবুর রহমান মাদানি"
    ABDULLAH_MAHMUD = "আব্দুল্লাহ মাহমুদ", "আব্দুল্লাহ মাহমুদ"
    ABDUL_GHANI_MADANI = "আব্দুল গনি মাদানি", "আব্দুল গনি মাদানি"
    GOLAM_RABBANI = "গোলাম রাব্বানী", "গোলাম রাব্বানী"
    MUSLEHUDDIN_BIN_SIRAJUL_ISLAM = "মুসলেহউদ্দিন বিন সিরাজুল ইসলাম", "মুসলেহউদ্দিন বিন সিরাজুল ইসলাম"
    MUHAMMAD_AL_FIROZ = "মুহাম্মদ আল ফিরোজ", "মুহাম্মদ আল ফিরোজ"



class DeliveryMediumChoices(models.TextChoices):
    POST = "পোস্ট", "পোস্ট"
    COURIER = "কুরিয়ার", "কুরিয়ার"

