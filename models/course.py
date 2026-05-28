# models/course.py
# TODO: Translate -  Section ۱۴: Learning Hub - آموزش و آکادمی

from . import db
from datetime import datetime, timedelta
from enum import Enum

class CourseLevel(Enum):
    BEGINNER = 'beginner'  # TODO: Translate -  مقدماتی
    INTERMEDIATE = 'intermediate'  # TODO: Translate -  متوسط
    ADVANCED = 'advanced'  # TODO: Translate -  پیشرفته
    EXPERT = 'expert'  # TODO: Translate -  تخصصی

class CourseCategory(Enum):
    EXPORT_BASICS = 'export_basics'  # TODO: Translate -  اصول صادرات
    IMPORT_BASICS = 'import_basics'  # TODO: Translate -  اصول واRejectات
    CUSTOMS_REGULATIONS = 'customs_regulations'  # TODO: Translate -  مقررات گمرکی
    INTERNATIONAL_LAW = 'international_law'  # TODO: Translate -  حقوق بین‌الملل
    LOGISTICS = 'logistics'  # TODO: Translate -  لجستیک و حمل‌ونقل
    MARKETING = 'marketing'  # TODO: Translate -  بازاریابی بین‌الملل
    FINANCE = 'finance'  # TODO: Translate -  مالی و Payment
    COUNTRY_SPECIFIC = 'country_specific'  # TODO: Translate -  ویژه کشور خاص
    INDUSTRY_SPECIFIC = 'industry_specific'  # TODO: Translate -  ویژه صنعت خاص

class ContentType(Enum):
    VIDEO = 'video'
    ARTICLE = 'article'
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'
    LIVE_WEBINAR = 'live_webinar'
    PDF = 'pdf'
    EXTERNAL_LINK = 'external_link'

class CertificateType(Enum):
    COMPLETION = 'completion'  # TODO: Translate -  گواهی تکمیل دوره
    ACHIEVEMENT = 'achievement'  # TODO: Translate -  گواهی Successیت (نمره بالا)
    PARTICIPATION = 'participation'  # TODO: Translate -  گواهی مشارکت در وبینار

class Course(db.Model):
    """
    دوره آموزشی - بخش ۱۴
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # TODO: Translate -  Information پایه
    title_fa = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    title_ar = db.Column(db.String(200))
    
    description_fa = db.Column(db.Text)
    description_en = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    
    # TODO: Translate -  دسته‌بندی
    category = db.Column(db.Enum(CourseCategory), nullable=False)
    level = db.Column(db.Enum(CourseLevel), default=CourseLevel.BEGINNER)
    
    # TODO: Translate -  مدرس
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    instructor_name_fa = db.Column(db.String(100))
    instructor_name_en = db.Column(db.String(100))
    instructor_bio = db.Column(db.Text)
    
    # TODO: Translate -  محتوا
    thumbnail = db.Column(db.String(500))  # TODO: Translate -  تصویر شاخص
    trailer_url = db.Column(db.String(500))  # TODO: Translate -  لینک تریلر
    
    # TODO: Translate -  Time‌بندی
    duration_minutes = db.Column(db.Integer, default=0)  # TODO: Translate -  مدت کل (دقیقه)
    estimated_days = db.Column(db.Integer)  # TODO: Translate -  روزهای تخمینی برای تکمیل
    
    # TODO: Translate -  Price‌گذاری
    price = db.Column(db.Numeric(10, 2), default=0)  # TODO: Translate -  Price به دلار
    currency = db.Column(db.String(3), default='USD')
    is_free = db.Column(db.Boolean, default=False)
    
    #  Status
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    is_featured = db.Column(db.Boolean, default=False)
    
    # TODO: Translate -  آمار
    enrolled_count = db.Column(db.Integer, default=0)
    completed_count = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Numeric(3, 2), default=0)
    rating_count = db.Column(db.Integer, default=0)
    
    # TODO: Translate -  پیش‌نیازها
    prerequisites = db.Column(db.JSON)  # TODO: Translate -  List دوره‌های پیش‌نیاز
    target_audience = db.Column(db.Text)  # TODO: Translate -  مخاطبان هدف
    
    # TODO: Translate -  سرفصل‌ها
    syllabus = db.Column(db.JSON)  # TODO: Translate -  ساختار دوره
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # TODO: Translate -  روابط
    instructor = db.relationship('User', backref=db.backref('taught_courses', lazy='dynamic'))
    modules = db.relationship('CourseModule', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='course', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title_fa': self.title_fa,
            'title_en': self.title_en,
            'category': self.category.value,
            'level': self.level.value,
            'duration_minutes': self.duration_minutes,
            'is_free': self.is_free,
            'price': float(self.price) if self.price else 0,
            'enrolled_count': self.enrolled_count,
            'average_rating': float(self.average_rating) if self.average_rating else 0,
            'thumbnail': self.thumbnail,
            'instructor_name': self.instructor_name_fa,
        }


class CourseModule(db.Model):
    """
    ماژول/فصل دوره - بخش ۱۴
    """
    __tablename__ = 'course_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    
    title_fa = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    
    description = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)  # TODO: Translate -  ترتیب View
    
    duration_minutes = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TODO: Translate -  روابط
    lessons = db.relationship('CourseLesson', backref='module', lazy='dynamic', cascade='all, delete-orphan', order_by='CourseLesson.order_index')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title_fa': self.title_fa,
            'order_index': self.order_index,
            'duration_minutes': self.duration_minutes,
            'lessons_count': self.lessons.count(),
        }


class CourseLesson(db.Model):
    """
    درس/محتوای داخل ماژول - بخش ۱۴
    """
    __tablename__ = 'course_lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('course_modules.id'), nullable=False, index=True)
    
    title_fa = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    
    content_type = db.Column(db.Enum(ContentType), nullable=False)
    
    # TODO: Translate -  محتوا
    video_url = db.Column(db.String(500))  # TODO: Translate -  برای ویدیو
    video_duration = db.Column(db.Integer)  # TODO: Translate -  مدت ویدیو (ثانیه)
    
    article_content = db.Column(db.Text)  # TODO: Translate -  برای مقاله
    
    quiz_data = db.Column(db.JSON)  # TODO: Translate -  سوالات آزمون
    passing_score = db.Column(db.Integer, default=70)  # TODO: Translate -  نمره قبولی (درصد)
    
    file_url = db.Column(db.String(500))  # TODO: Translate -  برای PDF و File‌ها
    external_url = db.Column(db.String(500))  # TODO: Translate -  لینک خارجی
    
    order_index = db.Column(db.Integer, default=0)
    
    is_preview = db.Column(db.Boolean, default=False)  # TODO: Translate -  قابل مشاهده رایگان
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TODO: Translate -  آمار
    view_count = db.Column(db.Integer, default=0)
    completion_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title_fa': self.title_fa,
            'content_type': self.content_type.value,
            'video_duration': self.video_duration,
            'is_preview': self.is_preview,
            'order_index': self.order_index,
        }


class CourseEnrollment(db.Model):
    """
    ثبت‌نام کاربر در دوره - بخش ۱۴
    """
    __tablename__ = 'course_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    
    #  Status
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    
    # TODO: Translate -  پیشرفت
    progress_percentage = db.Column(db.Numeric(5, 2), default=0)
    completed_lessons = db.Column(db.JSON, default=[])  # TODO: Translate -  List ID درس‌های تکمیل‌شده
    
    # TODO: Translate -  Time‌بندی
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # TODO: Translate -  یادداشت‌ها
    notes = db.Column(db.Text)  # TODO: Translate -  یادداشت‌های User
    
    # TODO: Translate -  روابط
    user = db.relationship('User', backref=db.backref('course_enrollments', lazy='dynamic'))
    lesson_progress = db.relationship('LessonProgress', backref='enrollment', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_title': self.course.title_fa if self.course else None,
            'progress_percentage': float(self.progress_percentage) if self.progress_percentage else 0,
            'status': self.status,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class LessonProgress(db.Model):
    """
    پیشرفت کاربر در هر درس - بخش ۱۴
    """
    __tablename__ = 'lesson_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollments.id'), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_lessons.id'), nullable=False)
    
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    # TODO: Translate -  برای آزمون‌ها
    quiz_score = db.Column(db.Integer)  # TODO: Translate -  نمره کسب‌شده
    quiz_passed = db.Column(db.Boolean)
    quiz_attempts = db.Column(db.Integer, default=0)
    
    time_spent_seconds = db.Column(db.Integer, default=0)  # TODO: Translate -  Time صرف‌شده
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lesson = db.relationship('CourseLesson', backref='progress_records')
    
    __table_args__ = (db.UniqueConstraint('enrollment_id', 'lesson_id', name='unique_lesson_progress'),)


class Certificate(db.Model):
    """
    گواهینامه دوره - بخش ۱۴
    """
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    
    # TODO: Translate -  Type گواهی
    certificate_type = db.Column(db.Enum(CertificateType), nullable=False)
    
    # TODO: Translate -  نمره نهایی
    final_score = db.Column(db.Numeric(5, 2))
    
    #  Date
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # TODO: Translate -  Date انقضا (برای گواهی‌های موقت)
    
    #  File
    pdf_url = db.Column(db.String(500))  # TODO: Translate -  لینک Download PDF
    verification_code = db.Column(db.String(20), unique=True)  # TODO: Translate -  کد استعلام
    
    # TODO: Translate -  امضاها
    instructor_signature = db.Column(db.String(500))  # TODO: Translate -  تصویر امضای مدرس
    platform_signature = db.Column(db.String(500))  # TODO: Translate -  تصویر امضای پلتفرم
    
    is_verified = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)  # TODO: Translate -  View در پروFile عمومی
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TODO: Translate -  روابط
    user = db.relationship('User', backref=db.backref('certificates', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'certificate_number': self.certificate_number,
            'course_title': self.course.title_fa if self.course else None,
            'certificate_type': self.certificate_type.value,
            'final_score': float(self.final_score) if self.final_score else None,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'verification_code': self.verification_code,
            'pdf_url': self.pdf_url,
            'is_public': self.is_public,
        }


class Webinar(db.Model):
    """
    وبینار زنده - بخش ۱۴
    """
    __tablename__ = 'webinars'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title_fa = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200))
    
    description_fa = db.Column(db.Text)
    description_en = db.Column(db.Text)
    
    # TODO: Translate -  مدرس
    speaker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    speaker_name = db.Column(db.String(100))
    
    # TODO: Translate -  Time‌بندی
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # TODO: Translate -  لینک‌ها
    meeting_url = db.Column(db.String(500))  # TODO: Translate -  لینک Session
    recording_url = db.Column(db.String(500))  # TODO: Translate -  لینک ضبط شده
    
    # TODO: Translate -  ظرفیت
    max_participants = db.Column(db.Integer, default=100)
    
    #  Price
    price = db.Column(db.Numeric(10, 2), default=0)
    is_free = db.Column(db.Boolean, default=False)
    
    #  Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, live, completed, cancelled
    
    # TODO: Translate -  آمار
    registered_count = db.Column(db.Integer, default=0)
    attended_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    speaker = db.relationship('User', backref=db.backref('webinars', lazy='dynamic'))
    registrations = db.relationship('WebinarRegistration', backref='webinar', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title_fa': self.title_fa,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'status': self.status,
            'is_free': self.is_free,
            'registered_count': self.registered_count,
            'max_participants': self.max_participants,
        }


class WebinarRegistration(db.Model):
    """
    ثبت‌نام در وبینار - بخش ۱۴
    """
    __tablename__ = 'webinar_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    attendance_duration = db.Column(db.Integer)  # TODO: Translate -  مدت حضور (دقیقه)
    
    certificate_issued = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('webinar_id', 'user_id', name='unique_webinar_registration'),)
    
    user = db.relationship('User', backref=db.backref('webinar_registrations', lazy='dynamic'))


class LearningPath(db.Model):
    """
    مسیر یادگیری شخصی‌سازی‌شده - بخش ۱۴
    """
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # TODO: Translate -  دوره‌های پیشنهادی
    recommended_courses = db.Column(db.JSON)  # TODO: Translate -  List ID دوره‌ها
    
    # TODO: Translate -  پیشرفت کلی
    total_courses = db.Column(db.Integer, default=0)
    completed_courses = db.Column(db.Integer, default=0)
    progress_percentage = db.Column(db.Numeric(5, 2), default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('learning_paths', lazy='dynamic'))
