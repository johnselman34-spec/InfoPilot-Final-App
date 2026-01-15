import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Translation resources
const resources = {
  en: {
    translation: {
      // Navigation
      "nav.home": "Home",
      "nav.search": "Ultimate Search",
      "nav.marketplace": "Marketplace",
      "nav.groups": "Groups",
      "nav.pages": "Pages",
      "nav.chat": "Chat",
      "nav.profile": "Profile",
      "nav.settings": "Settings",
      "nav.admin": "Admin Control",
      "nav.logout": "Sign Out",
      
      // Common
      "common.loading": "Loading...",
      "common.save": "Save",
      "common.cancel": "Cancel",
      "common.delete": "Delete",
      "common.edit": "Edit",
      "common.search": "Search",
      "common.create": "Create",
      "common.submit": "Submit",
      "common.close": "Close",
      "common.yes": "Yes",
      "common.no": "No",
      "common.all": "All",
      "common.none": "None",
      
      // Auth
      "auth.signin": "Sign In",
      "auth.signup": "Sign Up",
      "auth.signout": "Sign Out",
      "auth.email": "Email",
      "auth.password": "Password",
      "auth.forgotPassword": "Forgot Password?",
      "auth.googleSignIn": "Continue with Google",
      "auth.createAccount": "Create Account",
      
      // Search
      "search.title": "Ultimate Search",
      "search.placeholder": "Enter search query...",
      "search.collate": "Collate",
      "search.results": "Results",
      "search.noResults": "No results found",
      "search.category": "Category",
      "search.protocol": "Protocol",
      "search.aggregation": "Aggregation",
      
      // Marketplace
      "marketplace.title": "Protocol Marketplace",
      "marketplace.browse": "Browse",
      "marketplace.sell": "Sell Protocol",
      "marketplace.purchases": "My Purchases",
      "marketplace.dashboard": "Seller Dashboard",
      "marketplace.bundles": "Protocol Bundles",
      "marketplace.buyNow": "Buy Now",
      "marketplace.price": "Price",
      "marketplace.sales": "Sales",
      "marketplace.featured": "Featured",
      
      // Chat
      "chat.title": "Chat",
      "chat.rooms": "Chat Rooms",
      "chat.newRoom": "New Room",
      "chat.typeMessage": "Type a message...",
      "chat.send": "Send",
      "chat.online": "Online",
      "chat.offline": "Offline",
      
      // Promotions
      "promo.book.title": "Letters to Evelyn",
      "promo.book.author": "by John Selman",
      "promo.book.tagline": "A Supernatural Thriller Comedy",
      "promo.book.buyNow": "Buy Now - $2.99",
      "promo.infopilot.title": "InfoPilot Explorer",
      "promo.infopilot.tagline": "World Wide Information Exchange",
      "promo.bistro.title": "Maestro Bistro",
      "promo.bistro.location": "Brunswick, Maine",
      "promo.toppilot": "Top Pilot Enterprises, Inc.",
      
      // Admin
      "admin.title": "Admin Dashboard",
      "admin.users": "Users",
      "admin.analytics": "Analytics",
      "admin.settings": "Settings",
      "admin.notifications": "Push Notifications"
    }
  },
  es: {
    translation: {
      // Navigation
      "nav.home": "Inicio",
      "nav.search": "Búsqueda Suprema",
      "nav.marketplace": "Mercado",
      "nav.groups": "Grupos",
      "nav.pages": "Páginas",
      "nav.chat": "Chat",
      "nav.profile": "Perfil",
      "nav.settings": "Configuración",
      "nav.admin": "Control Admin",
      "nav.logout": "Cerrar Sesión",
      
      // Common
      "common.loading": "Cargando...",
      "common.save": "Guardar",
      "common.cancel": "Cancelar",
      "common.delete": "Eliminar",
      "common.edit": "Editar",
      "common.search": "Buscar",
      "common.create": "Crear",
      "common.submit": "Enviar",
      "common.close": "Cerrar",
      "common.yes": "Sí",
      "common.no": "No",
      "common.all": "Todo",
      "common.none": "Ninguno",
      
      // Auth
      "auth.signin": "Iniciar Sesión",
      "auth.signup": "Registrarse",
      "auth.signout": "Cerrar Sesión",
      "auth.email": "Correo Electrónico",
      "auth.password": "Contraseña",
      "auth.forgotPassword": "¿Olvidó su contraseña?",
      "auth.googleSignIn": "Continuar con Google",
      "auth.createAccount": "Crear Cuenta",
      
      // Search
      "search.title": "Búsqueda Suprema",
      "search.placeholder": "Ingrese consulta de búsqueda...",
      "search.collate": "Cotejar",
      "search.results": "Resultados",
      "search.noResults": "No se encontraron resultados",
      "search.category": "Categoría",
      "search.protocol": "Protocolo",
      "search.aggregation": "Agregación",
      
      // Marketplace
      "marketplace.title": "Mercado de Protocolos",
      "marketplace.browse": "Explorar",
      "marketplace.sell": "Vender Protocolo",
      "marketplace.purchases": "Mis Compras",
      "marketplace.dashboard": "Panel de Vendedor",
      "marketplace.bundles": "Paquetes de Protocolos",
      "marketplace.buyNow": "Comprar Ahora",
      "marketplace.price": "Precio",
      "marketplace.sales": "Ventas",
      "marketplace.featured": "Destacado",
      
      // Chat
      "chat.title": "Chat",
      "chat.rooms": "Salas de Chat",
      "chat.newRoom": "Nueva Sala",
      "chat.typeMessage": "Escribe un mensaje...",
      "chat.send": "Enviar",
      "chat.online": "En Línea",
      "chat.offline": "Desconectado",
      
      // Promotions
      "promo.book.title": "Letters to Evelyn",
      "promo.book.author": "por John Selman",
      "promo.book.tagline": "Un Thriller Sobrenatural Cómico",
      "promo.book.buyNow": "Comprar - $2.99",
      "promo.infopilot.title": "InfoPilot Explorer",
      "promo.infopilot.tagline": "Intercambio Mundial de Información",
      "promo.bistro.title": "Maestro Bistro",
      "promo.bistro.location": "Brunswick, Maine",
      "promo.toppilot": "Top Pilot Enterprises, Inc.",
      
      // Admin
      "admin.title": "Panel de Administrador",
      "admin.users": "Usuarios",
      "admin.analytics": "Analíticas",
      "admin.settings": "Configuración",
      "admin.notifications": "Notificaciones Push"
    }
  },
  fr: {
    translation: {
      // Navigation
      "nav.home": "Accueil",
      "nav.search": "Recherche Ultime",
      "nav.marketplace": "Marché",
      "nav.groups": "Groupes",
      "nav.pages": "Pages",
      "nav.chat": "Chat",
      "nav.profile": "Profil",
      "nav.settings": "Paramètres",
      "nav.admin": "Admin",
      "nav.logout": "Déconnexion",
      
      // Common
      "common.loading": "Chargement...",
      "common.save": "Enregistrer",
      "common.cancel": "Annuler",
      "common.delete": "Supprimer",
      "common.edit": "Modifier",
      "common.search": "Rechercher",
      "common.create": "Créer",
      "common.submit": "Soumettre",
      "common.close": "Fermer",
      "common.yes": "Oui",
      "common.no": "Non",
      "common.all": "Tout",
      "common.none": "Aucun",
      
      // Promotions
      "promo.book.title": "Letters to Evelyn",
      "promo.book.author": "par John Selman",
      "promo.book.tagline": "Un Thriller Surnaturel Comique",
      "promo.book.buyNow": "Acheter - $2.99",
      "promo.infopilot.title": "InfoPilot Explorer",
      "promo.infopilot.tagline": "Échange Mondial d'Information",
      "promo.bistro.title": "Maestro Bistro",
      "promo.bistro.location": "Brunswick, Maine",
      "promo.toppilot": "Top Pilot Enterprises, Inc."
    }
  },
  de: {
    translation: {
      // Navigation
      "nav.home": "Startseite",
      "nav.search": "Ultimative Suche",
      "nav.marketplace": "Marktplatz",
      "nav.groups": "Gruppen",
      "nav.pages": "Seiten",
      "nav.chat": "Chat",
      "nav.profile": "Profil",
      "nav.settings": "Einstellungen",
      "nav.admin": "Admin",
      "nav.logout": "Abmelden",
      
      // Common
      "common.loading": "Laden...",
      "common.save": "Speichern",
      "common.cancel": "Abbrechen",
      "common.delete": "Löschen",
      "common.edit": "Bearbeiten",
      "common.search": "Suchen",
      "common.create": "Erstellen",
      "common.submit": "Senden",
      "common.close": "Schließen",
      
      // Promotions
      "promo.book.title": "Letters to Evelyn",
      "promo.book.author": "von John Selman",
      "promo.book.tagline": "Ein Übernatürlicher Thriller Komödie",
      "promo.book.buyNow": "Kaufen - $2.99",
      "promo.infopilot.title": "InfoPilot Explorer",
      "promo.infopilot.tagline": "Weltweiter Informationsaustausch",
      "promo.bistro.title": "Maestro Bistro",
      "promo.bistro.location": "Brunswick, Maine",
      "promo.toppilot": "Top Pilot Enterprises, Inc."
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('language') || 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;

// Language switcher helper
export const changeLanguage = (lang) => {
  i18n.changeLanguage(lang);
  localStorage.setItem('language', lang);
};

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
];
