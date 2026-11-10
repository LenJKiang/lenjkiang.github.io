// 只在正式网站启用；本地预览不发送访问或点击记录。
(() => {
  const settings = document.currentScript;
  if (!settings || window.location.origin !== settings.dataset.analyticsOrigin) return;
  const robots = document.querySelector('meta[name="robots"]');
  if (robots && /noindex/i.test(robots.content)) return;
  const endpoint = settings.dataset.goatcounter;
  if (!/^https:\/\/[a-z0-9][a-z0-9-]*\.goatcounter\.com\/count$/.test(endpoint || '')) return;
  const tracker = document.createElement('script');
  tracker.src = 'https://gc.zgo.at/count.js';
  tracker.async = true;
  tracker.dataset.goatcounter = endpoint;
  document.head.appendChild(tracker);
})();
