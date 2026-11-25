# Import all models here so SQLAlchemy's mapper registry can resolve every
# cross-model relationship string (e.g. relationship("User"), relationship("Notification"))
# regardless of which model file was the first to be imported.
from app.models.app_setting import AppSetting  # noqa: F401
from app.models.banner import Banner  # noqa: F401
from app.models.catalog import (  # noqa: F401
    CatalogCategorie,
    CatalogFamille,
    CatalogGamme,
    CatalogSousCategorie,
    CatalogSousFamille,
    CatalogType,
    OrgAgence,
    OrgSociete,
    OrgVille,
)
from app.models.notification import Notification  # noqa: F401
from app.models.order import Order, OrderLine, OrderStatusHistory  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.sync_log import SyncLog  # noqa: F401
from app.models.user import PasswordResetToken, ServiceToken, User  # noqa: F401
