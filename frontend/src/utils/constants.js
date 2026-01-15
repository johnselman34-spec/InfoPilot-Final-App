/**
 * API configuration and constants
 */

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
export const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

// Stripe Publishable Key - Only initialize if key exists
export const stripeKey = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;

// All Images - Including book images
export const IMAGES = {
  globe: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/utj2uh0i_global-network-world-globe-focusing-usa-symbolizing-data-transfer-worldwide-concept-data-transfer-global-connectivity-information-exchange-world-globe-usa-symbolism_918839-41653.jpg",
  author: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/5150hnhi_FB_IMG_1767397923842.jpg",
  bookCoverMain: "https://customer-assets.emergentagent.com/job_5fdf2820-b9a7-4458-b1a2-1b10e8aac7a0/artifacts/sz2m7z1e_ebook-1.jpg",
  bookCover1: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/kkmai0t8_Letters%20to%20Evelyn%20advertisement%201.jpg",
  bookCover2: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/2p3c884v_Letters%20to%20Evelyn%20advertisement%202.jpg",
  bookCover3: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/3qhi02pv_Letters%20to%20Evelyn%20advertisement%203.jpg",
  bookCover4: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/qxfza2d2_Letters%20to%20Evelyn%20advertisement%204.jpg"
};

// Book Info with 19 Five-Star Reviews
export const BOOK_INFO = {
  title: "Letters to Evelyn",
  author: "John Selman",
  tagline: "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
  genre: "A True Supernatural Thriller Comedy",
  years: "13 Years of Cosmic Chaos",
  rating: 5.0,
  reviewsCount: 19,
  price: "$2.99",
  amazonUrl: "https://a.co/d/atfpIds",
  sintraUrl: "https://www.Letters-to-Evelyn.sintra.site",
  officialUrl: "https://letterstoevelynbyjohnselmanii.com",
  readersFavorite Url: "https://readersfavorite.com/book-review/letters-to-evelyn",
  googleDriveUrl: "https://drive.google.com/file/d/1YFhr75fWLzF2nu6nYDgVKB0fjEzZ36Pt/view?usp=drivesdk",
  quotes: [
    { text: "A profound and unforgettable literary piece... poetic prose and introspective storytelling create an immersive reading experience that is as enlightening as it is emotionally resonant.", author: "Divine Zape, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "The author's imagination is off the charts. I did not think a novel combining science fiction, romance, and biblical characters could be achieved.", author: "Lesley Jones, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "Such a unique and wonderfully woven story that had me riveted from the moment I started reading it.", author: "Rabia Tanveer, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "A mesmerizing exploration of the human condition and the quest for meaning in a chaotic world.", author: "Readers' Favorite Review ⭐⭐⭐⭐⭐" },
    { text: "Selman's unwavering devotion to Evelyn is heartbreaking and inspiring, a light amidst the darkness.", author: "Professional Review ⭐⭐⭐⭐⭐" }
  ],
  // FUNNY TAGLINES - Extremely funny and convincing!
  funnyTaglines: [
    "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
    "Get yourself giggling in disoriented, stupefying hee-haw laughter! 😂",
    "Hurricane-force winds of laughter from the most skeptical of minds!",
    "Finally, an easy-to-read novella that flows - you won't be able to put it down!",
    "50+ zingers in succession. Bat-sh*t insane? Maybe. Unforgettable? DEFINITELY. 🚀",
    "Written by a U.S. Naval Officer who graduated FIRST in his class! 🎖️",
    "WARNING: May cause uncontrollable laughter, existential enlightenment, and the urge to buy more copies for friends! 📚",
    "What happens when a Navy pilot meets the supernatural? PURE CHAOS. And it's hilarious.",
    "13 years in the making. One man. One cosmic adventure. Zero regrets. 100% entertainment!",
    "If coffee could write a book, it still wouldn't be this energizing! ☕📖",
    "The book that makes The Twilight Zone look like a children's bedtime story!",
    "OPTIONED FOR FILM! Get it before Hollywood does! 🎬",
    "Part autobiography, part supernatural thriller, 100% unforgettable!",
    "Your brain will thank you. Your funny bone will propose marriage. 💍"
  ]
};

// MARKETPLACE PROMOTION - Funny and convincing copy
export const MARKETPLACE_PROMO = {
  headlines: [
    "🌍 WORLDWIDE MARKETPLACE: Where Protocols Become Profits!",
    "💰 Turn Your Research Into REAL Money - It's EASIER Than Finding Waldo!",
    "🚀 Sell Your Protocols, Buy Your Dreams!",
    "📈 From Zero to Hero: Your Protocol Empire Awaits!"
  ],
  taglines: [
    "Why keep your brilliant protocols to yourself? Share them with the world and make bank! 💵",
    "You spent hours researching. Now spend minutes getting PAID for it! 🤑",
    "The only marketplace where nerds become millionaires... okay, maybe hundredaires first. 🤓",
    "Every search protocol you create could be someone else's treasure. Sell it!",
    "90% goes to YOU. 10% keeps our servers from crying. Fair deal? We think so! 🖥️"
  ],
  ctaButtons: [
    "START SELLING NOW! 💸",
    "LIST YOUR FIRST PROTOCOL",
    "JOIN THE MARKETPLACE REVOLUTION",
    "BECOME A PROTOCOL MILLIONAIRE"
  ]
};

// PAY WHAT YOU WANT PROMOTION
export const PAY_WHAT_YOU_WANT_PROMO = {
  headlines: [
    "🆓 IT'S FREE! (Yes, Really. We Checked.)",
    "💰 Pay What You Want - Even Nothing!",
    "🎉 Free Access to the Most Powerful Search Tool Since Google!",
    "📖 No Subscription Fees. No Hidden Costs. Just Pure Research Power."
  ],
  taglines: [
    "We believe in karma. And also in not making you broke. Use InfoPilot FREE! 🆓",
    "Our competitors charge $99/month. We charge... whatever you feel like paying! 🤷‍♂️",
    "Free like puppies. Useful like having a research team. InfoPilot Explorer. 🐕📚",
    "Support us with $0.75/year if you want. Or don't. We'll still love you. 💜",
    "The app is FREE. The book is $2.99. Your newfound research powers? PRICELESS."
  ]
};

// TOP PILOT ENTERPRISES
export const COMPANY_INFO = {
  name: "Top Pilot Enterprises, Inc.",
  tagline: "Pioneering the Future of Information Discovery",
  mission: "Making the world's information accessible, searchable, and profitable for everyone."
};

// Pricing Info
export const SALE_PRICE = 0.75;
export const REGULAR_PRICE = 4.62;

// Reaction Types (Facebook-style)
export const REACTION_CONFIG = {
  like: { icon: "👍", label: "Like", color: "#3b82f6" },
  love: { icon: "❤️", label: "Love", color: "#ef4444" },
  haha: { icon: "😂", label: "Haha", color: "#eab308" },
  wow: { icon: "😮", label: "Wow", color: "#eab308" },
  sad: { icon: "😢", label: "Sad", color: "#eab308" },
  angry: { icon: "😠", label: "Angry", color: "#f97316" }
};
