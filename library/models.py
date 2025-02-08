from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, Group, Permission
from django_jalali.db import models as jmodels
# from users.models import LibraryUser
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image


class Province(models.Model):
    code = models.PositiveIntegerField(unique=True, verbose_name="کد استان")
    name = models.CharField(max_length=50, unique=True, verbose_name="استان")

    def __str__(self):
        return f"{self.code} - {self.name}"

class Region(models.Model):
    code = models.PositiveIntegerField(unique=True, verbose_name="کد منطقه")
    name = models.CharField(max_length=50, unique=True, verbose_name="منطقه")

    def __str__(self):
        return f"{self.code} - {self.name}"

class City(models.Model):
    code = models.PositiveIntegerField(verbose_name="کد شهر")
    name = models.CharField(max_length=100, verbose_name="شهر")
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name="cities", verbose_name="استان")
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="cities", verbose_name="منطقه")

    class Meta:
        unique_together = (("code", "province", "region"),)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Library(models.Model):    
    library_id = models.IntegerField(
        unique=True,
        primary_key=True,  # شناسه اصلی کتابخانه
        db_index=True
    )
    name = models.CharField(max_length=255)  # نام کتابخانه
    address = models.TextField(blank=True, null=True)  # آدرس (اختیاری)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, verbose_name="استان", default=1)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name="منطقه", default=1)
    city = models.ForeignKey(City, on_delete=models.PROTECT, verbose_name="شهر", default=1)
    created_at = jmodels.jDateTimeField(default=now, editable=False)  # تاریخ ایجاد
    updated_at = jmodels.jDateTimeField(auto_now=True)  # تاریخ ویرایش
    description = models.TextField(blank=True, null=True)  # توضیحات
    image = models.ImageField(upload_to='libraries/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # شماره تلفن
    email = models.EmailField(blank=True, null=True)  # ایمیل

    def __str__(self):
        return f"{self.library_id} - {self.name}"


class LibraryFloor(models.Model):
    library = models.ForeignKey(
        'Library',
        on_delete=models.CASCADE,
        related_name="floors",
        verbose_name="کتابخانه"
    )
    floor_code = models.CharField(max_length=10, verbose_name="کد طبقه")
    floor_name = models.CharField(max_length=50, verbose_name="نام طبقه", blank=True, null=True)

    def __str__(self):
        return f"{self.library.name} - طبقه {self.floor_code}"


class LibrarySection(models.Model):
    library_floor = models.ForeignKey(
        LibraryFloor,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="طبقه"
    )
    section_code = models.CharField(max_length=10, verbose_name="کد بخش")
    section_name = models.CharField(max_length=50, verbose_name="نام بخش", blank=True, null=True)

    def __str__(self):
        return f"{self.library_floor.library.name} - طبقه {self.library_floor.floor_code} - بخش {self.section_code}"

class LibraryNews(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='news')  # مرتبط با کتابخانه
    title = models.CharField(max_length=255)  # عنوان خبر
    content = models.TextField()  # متن خبر
    date_posted = models.DateTimeField(auto_now_add=True)  # تاریخ ثبت

class LibraryPhoto(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='libphotos')  # مرتبط با کتابخانه
    image = models.ImageField(upload_to='library_photos/', blank=True, null=True,)  # تصویر
    caption = models.CharField(max_length=255, blank=True, null=True)  # توضیح برای عکس


class StaffRole(models.TextChoices):
    LIBRARIAN = 'Librarian', 'کتابدار'
    MANAGER = 'Manager', 'مدیر'
    ASSISTANT = 'Assistant', 'دستیار'
    OTHER = 'Other', 'سایر'

class LibraryStaff(models.Model):
    library = models.ForeignKey(
        'Library', 
        on_delete=models.CASCADE, 
        related_name='staff'
    )  # مرتبط کردن کارمند به کتابخانه
    first_name = models.CharField(max_length=50)  # نام
    last_name = models.CharField(max_length=50)  # نام خانوادگی
    role = models.CharField(
        max_length=20, 
        choices=StaffRole.choices, 
        default=StaffRole.LIBRARIAN
    )  # نقش کارمند
    email = models.EmailField(blank=True, null=True)  # ایمیل
    phone = models.CharField(max_length=20, blank=True, null=True)  # شماره تماس
    image = models.ImageField(
        upload_to='library_staff/', 
        blank=True, 
        null=True
    )  # تصویر کارمند
    bio = models.TextField(blank=True, null=True)  # توضیحات یا بیوگرافی

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role}"

    class Meta:
        verbose_name = "کارمند کتابخانه"
        verbose_name_plural = "کارمندان کتابخانه"
    
class Author(models.Model):
    first_name = models.CharField(max_length=100)  # نام کوچک
    last_name = models.CharField(max_length=100)   # نام خانوادگی
    birth_date = jmodels.jDateField(null=True, blank=True)  # تاریخ تولد
    death_date = jmodels.jDateField(null=True, blank=True)  # تاریخ وفات

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Document(models.Model):
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="کتابخانه"
    )
    language = models.CharField(max_length=6, choices=[
        ('فارسی', 'فارسی'),
        ('EN', 'لاتین'),
    ], default='فارسی', verbose_name="زبان")
    
    # اطلاعات پدیدآورنده
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)  # ارتباط با مدل Author
    other_contributors = models.CharField(max_length=255, verbose_name="سایر پدیدآورندگان", blank=True, null=True)
    
    # نقش‌ها
    ROLE_CHOICES = [
        ('translator', 'مترجم'),
        ('گزدآورنده', 'گردآوردنده'),
        ('editor', 'تدوین'),
        ('supervisor', 'استاد راهنما'),
        ('advisor', 'استاد مشاور'),
        ('thesis_writer', 'پایان‌نامه نویس'),
        ('singer', 'آوازخوان'),
        ('programmer', 'برنامه نویس'),
        ('producer', 'تهیه کننده'),
        ('actor', 'بازیگر'),
        ('illustrator', 'تصویرگر'),
        ('photographer', 'عکاس'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name="نقش", blank=True, null=True)
    
    # اطلاعات عنوان
    title = models.CharField(max_length=500, verbose_name="عنوان")
    sub_title = models.CharField(max_length=500, verbose_name="عنوان فرعی", blank=True, null=True)
    uniform_title = models.CharField(max_length=500, verbose_name="عنوان قراردادی", blank=True, null=True)
    
    # نوع مدرک
    DOCUMENT_TYPE_CHOICES = [
        ('کتاب', 'کتاب'), 
        ('پایاننامه', 'پایاننامه'), 
        ('thesis_dr', 'رساله'),
        ('article', 'مقاله'), 
        ('deed', 'اسناد و مدارک'), 
        ('project', 'طرح ها و پروژه ها'),
        ('report', 'گزارش'), 
        ('etc', 'سایر منابع'), 
        ('multimedia', 'مولتی مدیا'),
    ]
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, verbose_name="نوع مدرک", default='book')
    reference_type = models.CharField(max_length=20, choices=[
        ('reference', 'مرجع'),
        ('non_reference', 'غیرمرجع'),
    ], verbose_name="نوع مرجعیت", default='non_reference')
    
    # اطلاعات نشر
    publication_year = models.PositiveIntegerField(verbose_name="سال نشر", blank=True, null=True)
    publication_place = models.CharField(max_length=35, verbose_name="محل نشر", blank=True, null=True)
    publisher = models.CharField(max_length=255, verbose_name="ناشر", blank=True, null=True)
    
    # شماره‌های شناسایی و فهرست‌نویسی    
    record_number = models.PositiveIntegerField(unique=True, verbose_name="شماره رکورد")
    document_number = models.PositiveIntegerField(verbose_name="شماره مدرک")
    isbn = models.CharField(max_length=25, verbose_name="شابک", blank=True, null=True)
    
    # مشخصات فیزیکی
    pages = models.CharField(max_length=255, verbose_name="تعداد صفحات", blank=True, null=True)
    edition = models.CharField(max_length=255, verbose_name="ویرایش", blank=True, null=True)
    
    # فهرست‌نویسی و دسته‌بندی
    main_entry = models.CharField(max_length=255, verbose_name="سرشناسه", blank=True, null=True)
    added_entry = models.CharField(max_length=255, verbose_name="شناسه افزوده", blank=True, null=True)
    added_entry2 = models.CharField(max_length=255, verbose_name="شناسه افزوده", blank=True, null=True)
    added_entry3 = models.CharField(max_length=255, verbose_name="شناسه افزوده", blank=True, null=True)
    subject = models.CharField(max_length=255, verbose_name="موضوع", blank=True, null=True)
    description = models.CharField(max_length=255, verbose_name="یادداشت", blank=True, null=True)    
    
    # دسته‌بندی‌ها
    lcc_classification = models.CharField(max_length=100, verbose_name="رده‌بندی کنگره", blank=True, null=True)
    lcc_main_class = models.CharField(max_length=100, verbose_name="رده اصلی کنگره", blank=True, null=True)
    lcc_cutter_number = models.CharField(max_length=50, verbose_name="شماره کاتر", blank=True, null=True)
    nlm_classification = models.CharField(max_length=100, verbose_name="رده پزشکی NLM", blank=True, null=True)
    dewey_classification = models.CharField(max_length=100, verbose_name="رده دیویی", blank=True, null=True)
    tannalgan = models.CharField(max_length=100, verbose_name="تنالگان", blank=True, null=True)
    
    # اطلاعات دیگر
    previous_reg = models.CharField(max_length=255, verbose_name="ثبتهای قبلی", blank=True, null=True)
    cataloger_info = models.CharField(max_length=255, verbose_name="فهرست نویس", blank=True, null=True)
    date_data_entry = jmodels.jDateField(auto_now=True, verbose_name="تاریخ ورود داده")

    # فایل‌های پیوست
    cover_image = models.ImageField(upload_to='documents/covers/', 
                                    verbose_name="عکس جلد", blank=True, null=True,
                                    default='documents/covers/default_cover.jpg')
    electronic_file = models.FileField(upload_to='documents/files/', verbose_name="فایل الکترونیکی", blank=True, null=True)

    access_policy = models.OneToOneField(
        'DocumentAccess', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='related_document'
    ) 

    def clean(self):
        # بررسی وجود مدرک مشابه با عنوان و نویسنده مشابه در همان کتابخانه
        if self.author:  # اطمینان از اینکه نویسنده تعیین شده است
            existing_document = Document.objects.filter(
                library=self.library,
                title=self.title,
                author__first_name=self.author.first_name,
                author__last_name=self.author.last_name
            ).exclude(id=self.id)  # exclude کردن خود مدرک (در صورتی که در حال ویرایش است)
            
            if existing_document.exists():
                raise ValidationError('مدرک با عنوان و نام نویسنده مشابه در این کتابخانه وجود دارد.')
    
    def save(self, *args, **kwargs):
        if not self.record_number:  # فقط اگر شماره رکورد تنظیم نشده باشد
            last_record = Document.objects.all().order_by('record_number').last()
            self.record_number = (last_record.record_number + 1) if last_record else 1

        # اعتبارسنجی قبل از ذخیره مدل
        self.full_clean()
        super().save(*args, **kwargs)    
        
    
class RegistrationNumber(models.Model):
    document = models.ForeignKey(
        'Document', 
        on_delete=models.CASCADE, 
        related_name='registration_numbers', 
        verbose_name="مدرک"
    )
    library = models.ForeignKey(
        'Library', 
        on_delete=models.CASCADE,
        verbose_name="کتابخانه"
    )
    number = models.CharField(
        max_length=50, 
        verbose_name="شماره ثبت",
        db_index=True
    )
    STATUS_CHOICES = [
        ('available', 'موجود'),
        ('loaned', 'امانت داده شده'),
        ('lost', 'گمشده'),
        ('weeding', 'وجین شده'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name="وضعیت مدرک"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    # فیلد مربوط به کد محل نگهداری که به صورت اتوماتیک تولید می‌شود
    location_code = models.CharField(max_length=255, unique=True, blank=True, null=True, verbose_name="کد محل نگهداری")
    
    # فیلد مربوط به QR Code (اختیاری)
    qr_code = models.ImageField(upload_to='documents/qrcodes/', blank=True, null=True, verbose_name="QR کد")
    
    # روابط انتخاب دستی برای طبقه و بخش
    library_floor = models.ForeignKey(
        LibraryFloor,
        on_delete=models.PROTECT,
        verbose_name="طبقه",
        null=True, blank=True,
        related_name="registration_numbers"
    )
    library_section = models.ForeignKey(
        LibrarySection,
        on_delete=models.PROTECT,
        verbose_name="بخش",
        null=True, blank=True,
        related_name="registration_numbers"
    )

    def generate_location_code(self):
        """
        تولید کد محل نگهداری بر اساس اطلاعات:
          [کد استان]-[کد منطقه]-[کد شهر]-[شناسه کتابخانه]-[کد طبقه]-[کد بخش]-[شماره ثبت]
        فرض می‌کنیم:
         - در مدل Library اطلاعات استان، منطقه و شهر به صورت رابطه‌ای به مدل‌های Province, Region, City موجود است.
         - کدهای عددی استان، منطقه و شهر در فیلد code هر مدل ذخیره شده‌اند.
         - شناسه کتابخانه (library_id) نیز به صورت عددی موجود است.
         - کد طبقه و کد بخش از فیلدهای library_floor.floor_code و library_section.section_code گرفته می‌شود.
        """
        library = self.document.library
        
        province_code = str(library.province.code).zfill(2) if library.province and library.province.code is not None else "00"
        region_code   = str(library.region.code).zfill(2) if library.region and library.region.code is not None else "00"
        city_code     = str(library.city.code).zfill(3)   if library.city and library.city.code is not None else "000"
        
        library_code  = str(library.library_id).zfill(3)
        
        # طبقه و بخش باید از فیلدهای انتخاب شده گرفته شوند
        floor_code = self.library_floor.floor_code if self.library_floor and self.library_floor.floor_code else "00"
        section_code = self.library_section.section_code if self.library_section and self.library_section.section_code else "00"
        
        reg_number = self.number.strip().zfill(3) if self.number else "000"
        
        return f"{province_code}-{region_code}-{city_code}-{library_code}-{floor_code}-{section_code}-{reg_number}"

    def save(self, *args, **kwargs):
        # اطمینان از مقداردهی کتابخانه از طریق مدرک:
        if not self.document or not self.document.library:
            raise ValueError("Library cannot be null.")
        self.library = self.document.library
        self.number = self.number.strip()

        # تولید QR Code (اختیاری)
        qr_data = f"Document: {self.document.title} | ثبت: {self.number} | کتابخانه: {self.library.name}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        file_name = f"qrcode_{self.document.id}_{self.number}.png"
        self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)

        # تولید کد محل نگهداری در صورت خالی بودن آن
        if not self.location_code:
            self.location_code = self.generate_location_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.number

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'library'],
                name='unique_registration_number_in_library'
            )
        ]



class Member(AbstractUser):
    library = models.ForeignKey('Library', on_delete=models.CASCADE, null=True)  # ارتباط با کتابخانه
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    membership_id = models.CharField(max_length=50, unique=True)  # شناسه عضویت منحصر به فرد
    join_date = models.DateField(default=timezone.now)  # تاریخ عضویت
    member_type = models.CharField(max_length=50, choices=[
        ('student', 'دانشجو'),
        ('faculty', 'هیئت علمی'),
        ('staff', 'کارمند'),
        ('free_member', 'عضو آزاد'),
    ], verbose_name="نوع عضویت", default='student')
    email = models.EmailField(verbose_name="ایمیل", blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name="آدرس", blank=True, null=True)
    father_name = models.CharField(max_length=100, verbose_name="نام پدر", blank=True, null=True)
    national_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="کد ملی")
    birth_date = models.DateField(verbose_name="تاریخ تولد", blank=True, null=True)  # سال/ماه/روز
    gender = models.CharField(max_length=10, choices=[
        ('male', 'مرد'),
        ('female', 'زن'),
    ], verbose_name="جنسیت", blank=True, null=True)
    student_id = models.CharField(max_length=50, verbose_name="شماره دانشجویی", blank=True, null=True)
    personnel_number = models.CharField(max_length=50, verbose_name="شماره پرسنلی", blank=True, null=True)
    field_of_study = models.CharField(max_length=100, verbose_name="رشته تحصیلی", blank=True, null=True)
    degree = models.CharField(max_length=100, verbose_name="مدرک تحصیلی", blank=True, null=True)
    job = models.CharField(max_length=100, verbose_name="شغل", blank=True, null=True)
    nationality = models.CharField(max_length=100, verbose_name="ملیت", default='ایرانی')
    university = models.CharField(max_length=100, verbose_name="دانشگاه", blank=True, null=True)

    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('blocked', 'مسدود'),
        ('graduated', 'فارغ‌التحصیل'),
    ]
    member_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="وضعیت اعتبار عضو"
    )

    # فیلد عکس پروفایل
    profile_image = models.ImageField(
        upload_to='members/profile_images/',
        verbose_name="عکس پروفایل",
        blank=True,
        null=True,
        default='members/profile_images/default_profile.jpg'
    )

    # افزودن related_name برای جلوگیری از تداخل
    groups = models.ManyToManyField(Group, related_name="member_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="member_permissions_set", blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.membership_id}"

    REQUIRED_FIELDS = ['email', 'national_code', 'first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.membership_id
        super().save(*args, **kwargs)

        

def default_due_date():
    return datetime.now().date() + timedelta(days=15)

def default_reservation_expiry():
    return datetime.now() + timedelta(days=7)

class Loan(models.Model):
    registration_number = models.ForeignKey(
        'RegistrationNumber', 
        on_delete=models.CASCADE,
        null=True, 
        verbose_name="شماره ثبت"
    )
    member = models.ForeignKey(
        'Member', 
        on_delete=models.CASCADE, 
        verbose_name="عضو"
    )
    loan_date = models.DateField(
        default=now, 
        verbose_name="تاریخ امانت"
    )
    due_date = models.DateField(
        default=default_due_date, 
        verbose_name="تاریخ مهلت بازگشت"
    )
    return_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="تاریخ بازگشت"
    )
    is_returned = models.BooleanField(
        default=False, 
        verbose_name="بازگردانده شده"
    )
    debt = models.IntegerField(
        default=0, 
        verbose_name="بدهی (تومان)"
    )
    # وضعیت مالی عضو
    FINANCIAL_STATUS_CHOICES = [
        ('debtor', 'بدهکار'),
        ('no_debt', 'عدم بدهی'),
    ]
    financial_status = models.CharField(
        max_length=10,
        choices=FINANCIAL_STATUS_CHOICES,
        default='no_debt',
        verbose_name="وضعیت مالی"
    )
    STATUS_CHOICES = [
        ('loaned', 'امانت داده شده'),
        ('returned', 'بازگردانده شده'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='loaned',
    )

    class Meta:
        verbose_name = "امانت"
        verbose_name_plural = "امانات"

    def __str__(self):
        return f"{self.document.title} - {self.member.first_name} {self.member.last_name}"
        # return f"Loan of {self.registration_number.number} to {self.member}"

    def calculate_real_return_date(self):
        """
        محاسبه تاریخ واقعی بازگشت بر اساس تاریخ امانت و مدت زمان مهلت
        """
        return self.loan_date + timedelta(days=15) if self.loan_date else None

    def calculate_debt(self):
        """
        محاسبه میزان بدهکاری بر اساس تعداد روزهای تأخیر
        """
        today = now().date()
        delay_days = 0

        if not self.return_date and today > self.due_date:
            # اگر مدرک هنوز بازگردانده نشده و تاریخ فعلی از تاریخ مهلت بازگشت گذشته است
            delay_days = (today - self.due_date).days
        elif self.return_date and self.return_date > self.due_date:
            # اگر مدرک بازگردانده شده اما دیرتر از تاریخ مهلت بازگشت باشد
            delay_days = (self.return_date - self.due_date).days
        
        # محاسبه بدهی
        late_fee_per_day = 200
        return delay_days * late_fee_per_day

    def save(self, *args, **kwargs):
        """
        ذخیره مدل با محاسبه بدهی و مدیریت رزرو فعال
        """
        # محاسبه بدهی
        self.debt = self.calculate_debt()
        super().save(*args, **kwargs)


class Reservation(models.Model):
    # ارتباط با عضو
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    
    # ارتباط با مدرک
    document = models.ForeignKey('Document', on_delete=models.CASCADE)
    
    # تاریخ رزرو
    reservation_date = models.DateTimeField(default=datetime.now)
    
    # تاریخ مهلت رزرو (مثلاً ۷ روز)
    reservation_expiry = models.DateTimeField(default=default_reservation_expiry)
    
    # وضعیت رزرو
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('canceled', 'لغو شده'),
        ('completed', 'تکمیل شده'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    def __str__(self):
        return f"Reservation of {self.document} by {self.member}"

    # بررسی اینکه آیا رزرو منقضی شده است یا خیر
    def is_expired(self):
        return datetime.now() > self.reservation_expiry
    

class DocumentAccess(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name="accesspolicy")
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('full', 'دسترسی کامل'),
            ('partial', 'دسترسی جزئی'),
            ('restricted', 'محدود'),
        ],
        default='restricted',
        verbose_name="نوع دسترسی"
    )
    preview_pages = models.PositiveIntegerField(
        verbose_name="تعداد صفحات قابل مشاهده",
        null=True,
        blank=True,
        help_text="تعداد صفحاتی که برای پیش‌نمایش قابل دسترسی است (در صورت محدود بودن)"
    )
    is_for_sale = models.BooleanField(default=False, verbose_name="قابل فروش")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="قیمت",
        help_text="قیمت فروش فایل در صورت قابل فروش بودن"
    )

    def clean(self):
        # اعتبارسنجی قیمت در صورتی که مدرک برای فروش باشد
        if self.is_for_sale and not self.price:
            raise ValidationError("برای فروش، باید قیمت تعیین شود.")
        # محدودیت در دسترسی جزئی
        if self.access_type == 'partial' and not self.preview_pages:
            raise ValidationError("برای دسترسی جزئی، باید تعداد صفحات پیش‌نمایش مشخص شود.")

    def __str__(self):
        return f"سیاست دسترسی {self.document.title}"

