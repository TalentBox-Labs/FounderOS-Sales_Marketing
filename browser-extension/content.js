/* ── Content script for Revenue OS Extension ── */

function extractLinkedInProfile() {
  // Try multiple selectors to find profile name
  const nameSelectors = [
    'h1',                                                   // generic fallback
    '.text-heading-xlarge',                                 // LinkedIn new layout
    '.profile-card-name',                                   // old layout
    '.profile-topcard-person-name',                         // alternate layout
    '[data-anonymize="person-name"]',
  ];

  let name = '';
  for (const sel of nameSelectors) {
    const el = document.querySelector(sel);
    if (el && el.textContent.trim()) {
      name = el.textContent.trim();
      break;
    }
  }

  // If no name found via selectors, try the <title> tag
  if (!name) {
    const titleEl = document.querySelector('title');
    if (titleEl) {
      const t = titleEl.textContent.trim();
      // LinkedIn titles are like "John Doe | LinkedIn" or "John Doe - ..."
      const match = t.match(/^([^(|]+)/);
      if (match) name = match[1].trim();
    }
  }

  // Title / Headline
  const titleSelectors = [
    '.text-body-medium',                                     // new layout
    '.profile-card-headline',
    '.profile-topcard-headline',
    '[data-anonymize="headline"]',
  ];
  let title = '';
  for (const sel of titleSelectors) {
    const el = document.querySelector(sel);
    if (el && el.textContent.trim()) {
      title = el.textContent.trim();
      break;
    }
  }

  // Company (look for current position)
  const companySelectors = [
    '.profile-topcard-company-name',
    '.profile-card-company',
    '.pv-top-card--experience-list-item',
    'a[data-anonymize="company-name"]',
    '.experience-section .pv-entity__secondary-title',
  ];
  let company = '';
  for (const sel of companySelectors) {
    const el = document.querySelector(sel);
    if (el && el.textContent.trim()) {
      company = el.textContent.trim();
      break;
    }
  }

  // Fallback: look for "at Company" pattern in headline
  if (!company && title) {
    const match = title.match(/\bat\s+(.+?)(?:\s*[—–-]|\s*$)/);
    if (match) company = match[1].trim();
  }

  const url = window.location.href.split('?')[0];

  return { name, title, company, url };
}

// Listen for popup requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractProfile') {
    const profile = extractLinkedInProfile();
    sendResponse(profile);
  }
});
