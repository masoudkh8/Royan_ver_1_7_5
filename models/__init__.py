# models/__init__.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models

from .user import User, UserProfile
from .order import Order
from .notification import Notification
from .message import Message
from .provider import DataProvider
from .port import Port
from .premium_request import PremiumRequest
from .magazine import Magazine, MagazineIssue, SponsorshipRequest, AdvertisementRequest, Subscription

# New models for 16-section platform
from .trust_score import TrustScore
from .gamification import UserBadge, UserProgress, SeasonalChallenge, ChallengeParticipant
from .trade_credit import TradeCreditAccount, CreditTransaction, CreditRule
from .consortium import ConsortiumProject, ConsortiumMember, ConsortiumContract, PartnerMatch

# TODO: Translate -  Marketplace & Products (Section ۹)
from .product import Product, RFQ, RFQProposal, ProductComparison, FavoriteProduct

# TODO: Translate -  Financial Layer (Section ۱۰)
from .wallet import Wallet, WalletTransaction, EscrowTransaction, ExchangeRate, FinancialReport

# TODO: Translate -  Learning Hub (Section ۱۴)
from .course import Course, CourseModule, CourseLesson, CourseEnrollment, LessonProgress, Certificate, Webinar, WebinarRegistration, LearningPath

# TODO: Translate -  CRM & Leads (Section ۱۲)
from .lead import Lead, LeadInteraction, LeadTask, Campaign, CampaignLead, CampaignAnalytics, EmailTemplate, AutomationRule

# TODO: Translate -  Integrations (Section ۱۱)
from .integration import ExternalIntegration, IntegrationLog, WebhookSubscription, WebhookDelivery, LinkedInProfile, LinkedInPost, WhatsAppContact, LogisticsProvider, LogisticsQuote, APICache

# TODO: Translate -  AI Core (Section ۱)
from .ai_chat import Conversation, ChatMessage, AIRecommendation, CustomizationProfile, ContentGenerationRequest

# TODO: Translate -  Smart Map & Logistics (Section ۲)
from .smart_map import Country, CustomsData, RiskEvent, TradeRoute, ShipmentTracking

# TODO: Translate -  i18n & Localization (Section ۱۳)
from .i18n import Language, TranslationKey, Translation, LocalizationSettings

# TODO: Translate -  Data Intelligence (Section ۸)
from .data_intelligence import MarketTrend, CompetitorAnalysis, DemandForecast, TradeStatistic, CustomReport, DataAlert

# TODO: Translate -  Social Network (Section سوشال - مرحله ۱)
from .social import Follow, Post, Comment, Like, update_user_relationships

# TODO: Translate -  Exhibition Hall (Viewگاه آنلاین - مرحله ۲)
from .exhibition import (
    Exhibition, Booth, BoothVisit, BoothInteraction, BoothAppointment, ExhibitionVisit,
    ExhibitionStatus, BoothType,
    init_exhibition_db
)

# TODO: Translate -  Trading Hall (تالار معاملاتی - مرحله ۲)
from .trading import (
    TradingPair, TradingWallet, TradingWalletTransaction, TradeOrder, Trade, MarketData, TradingSetting,
    OrderType, OrderSide, OrderStatus,
    init_trading_db
)

# TODO: Translate -  Authentication & Security Models (امنیت و Authentication)
from .auth import PasswordResetToken, LoginSession, ActivityLog, EmailVerificationToken, TwoFactorBackupCode

# Initialize social relationships after all models are imported
update_user_relationships()