// Privacy Settings
user_pref("privacy.donottrackheader.enabled", true);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("privacy.trackingprotection.socialtracking.enabled", true);
user_pref("privacy.trackingprotection.emailtracking.enabled", true);

// Strict Tracking Protection (Replaces some legacy settings)
user_pref("browser.contentblocking.category", "strict");
user_pref("network.cookie.cookieBehavior", 5); // Total Cookie Protection
user_pref("privacy.partition.network_state.ocsp_cache", true);

// Privacy Preserving Attribution (PPA)
// Disable Mozilla's new ad measurement system
user_pref("dom.private-attribution.submission.enabled", false);

// Global Privacy Control
user_pref("privacy.globalprivacycontrol.enabled", true);
user_pref("privacy.globalprivacycontrol.functionality.enabled", true);

// Fingerprinting Settings
// Stabilized protections
user_pref("privacy.fingerprintingProtection", true);
user_pref("privacy.fingerprintingProtection.pbmode", true);
user_pref("privacy.query_stripping.enabled", true);
user_pref("privacy.query_stripping.enabled.pbmode", true);
user_pref("dom.battery.enabled", false);
user_pref("canvas.capturestream.enabled", false);

// Passwords & Clearing
user_pref("signon.rememberSignons", false);
user_pref("privacy.clearOnShutdown.offlineApps", false);
user_pref("privacy.sanitize.sanitizeOnShutdown", false);
user_pref("privacy.clearOnShutdown.cookies", false);

// Geolocation
user_pref("geo.provider.network.url", "https://location.services.mozilla.com/v1/geolocate?key=%MOZILLA_API_KEY%");
user_pref("geo.provider.use_gpsd", false);
user_pref("geo.provider.use_geoclue", false);

// Security Settings
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("dom.security.https_only_mode", true);
user_pref("dom.security.https_only_mode_ever_enabled", true);

// Network Settings
user_pref("network.dns.disablePrefetch", true);
user_pref("network.prefetch-next", false);
user_pref("network.predictor.enabled", false);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("network.http.referer.disallowCrossSiteRelaxingDefault.top_navigation", true);
user_pref("network.trr.mode", 3);
user_pref("network.trr.uri", "https://dns.quad9.net/dns-query");
user_pref("network.trr.custom_uri", "https://dns.quad9.net/dns-query");
user_pref("network.dns.echconfig.enabled", true);
user_pref("network.dns.http3_echconfig.enabled", true);

// Content and New Tab Settings
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.activity-stream.feeds.snippets", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
user_pref("browser.newtabpage.activity-stream.default.sites", "");
user_pref("browser.newtabpage.pinned", "[]");
user_pref("browser.tabs.firefox-view", false);
user_pref("extensions.pocket.enabled", false);
user_pref("browser.newtabpage.activity-stream.showWeather", false);
user_pref("browser.messaging-system.whatsNewPanel.enabled", false);

// Context Search & Suggest
user_pref("browser.search.suggest.enabled", false);
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.sponsored", false);
user_pref("browser.urlbar.suggest.weather", false);
user_pref("browser.urlbar.suggest.engines", false);
user_pref("browser.urlbar.suggest.calculator", true); // Local parsing only
user_pref("browser.urlbar.trending.featureGate", false);

// AI Chatbot Settings (Recent Additions)
// Ensure AI Chat features in the sidebar or URL bar are disabled
user_pref("browser.ml.enable", false);
user_pref("browser.ml.chat.enabled", false);
user_pref("browser.ml.chat.shortcuts", false);
user_pref("browser.ml.linkPreview.enabled", false);
user_pref("browser.tabs.groups.smart.enabled", false);

// Data Collection and Telemetry
user_pref("browser.discovery.enabled", false);
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.server", "");
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.coverage.opt-out", true);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.ping-centre.telemetry", false);