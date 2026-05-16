/* Utilidades globales UX para flujos transaccionales */
(function () {
	function beginButtonLoading(button, loadingText) {
		if (!button) return null;
		var state = {
			text: button.textContent,
			disabled: button.disabled,
		};
		button.disabled = true;
		if (loadingText) {
			button.textContent = loadingText;
		}
		return state;
	}

	function endButtonLoading(button, state, finalDisabled) {
		if (!button || !state) return;
		button.textContent = state.text;
		button.disabled = typeof finalDisabled === 'boolean' ? finalDisabled : state.disabled;
	}

	function fetchWithTimeout(url, options, timeoutMs) {
		var timeout = typeof timeoutMs === 'number' ? timeoutMs : 15000;
		var controller = new AbortController();
		var signal = controller.signal;
		var timer = setTimeout(function () {
			controller.abort();
		}, timeout);

		var opts = Object.assign({}, options || {}, { signal: signal });

		return fetch(url, opts).finally(function () {
			clearTimeout(timer);
		});
	}

	function setNetworkBanner(isOnline) {
		var banner = document.getElementById('network-status-banner');
		if (!banner) return;

		if (isOnline) {
			banner.classList.add('hidden');
			banner.textContent = '';
			return;
		}

		banner.textContent = 'Sin conexion a internet. Algunas operaciones pueden fallar.';
		banner.classList.remove('hidden');
		announce('Sin conexion a internet. Algunas operaciones pueden fallar.', 'assertive');
	}

	function announce(message, politeness) {
		if (!message) return;
		var mode = politeness === 'assertive' ? 'assertive' : 'polite';
		var targetId = mode === 'assertive' ? 'app-live-assertive' : 'app-live-polite';
		var region = document.getElementById(targetId);
		if (!region) return;

		region.textContent = '';
		setTimeout(function () {
			region.textContent = String(message);
		}, 20);
	}

	function initNetworkBanner() {
		setNetworkBanner(navigator.onLine);
		window.addEventListener('online', function () { setNetworkBanner(true); });
		window.addEventListener('offline', function () { setNetworkBanner(false); });
	}

	function toggleSidebar() {
		var sidebar = document.getElementById('sidebar');
		var overlay = document.getElementById('sidebar-overlay');
		if (!sidebar || !overlay) return;
		sidebar.classList.toggle('-translate-x-full');
		overlay.classList.toggle('open');
	}

	function initSidebar() {
		document.querySelectorAll('[data-sidebar-toggle]').forEach(function (button) {
			button.addEventListener('click', toggleSidebar);
		});

		var sidebarOverlay = document.getElementById('sidebar-overlay');
		if (sidebarOverlay) {
			sidebarOverlay.addEventListener('click', toggleSidebar);
		}

		document.querySelectorAll('#sidebar a.sidebar-link').forEach(function (link) {
			link.addEventListener('click', function () {
				if (window.innerWidth < 1024) toggleSidebar();
			});
		});
	}

	function initUserDropdown() {
		var userButton = document.getElementById('user-dropdown-button');
		var userMenu = document.getElementById('user-dropdown-menu');
		if (!userButton || !userMenu) return;

		userButton.addEventListener('click', function (e) {
			e.stopPropagation();
			userMenu.classList.toggle('hidden');
			userButton.setAttribute('aria-expanded', userMenu.classList.contains('hidden') ? 'false' : 'true');
		});

		document.addEventListener('click', function (e) {
			if (!userButton.contains(e.target) && !userMenu.contains(e.target)) {
				userMenu.classList.add('hidden');
				userButton.setAttribute('aria-expanded', 'false');
			}
		});
	}

	function showToast(message, type) {
		var toastType = type || 'info';
		var container = document.getElementById('toast-container');
		if (!container) return;

		var toast = document.createElement('div');
		toast.className = 'flex items-center justify-between p-4 rounded-lg shadow-lg max-w-sm w-full transform translate-x-full transition-transform duration-300';
		var colors = {
			success: 'bg-green-500 text-white',
			error: 'bg-red-500 text-white',
			warning: 'bg-yellow-500 text-black',
			info: 'bg-blue-500 text-white'
		};
		toast.className += ' ' + (colors[toastType] || colors.info);
		var icons = { success: '&#10003;', error: '&#10007;', warning: '&#9888;', info: '&#8505;' };
		toast.innerHTML = '<div class="flex items-center"><span class="mr-2 text-lg">' + (icons[toastType] || icons.info) + '</span><span class="text-sm">' + message + '</span></div><button type="button" data-toast-close class="ml-4 hover:opacity-75"><svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>';
		container.appendChild(toast);

		announce(message, toastType === 'error' ? 'assertive' : 'polite');

		setTimeout(function () {
			toast.classList.remove('translate-x-full');
		}, 100);
		setTimeout(function () {
			toast.classList.add('translate-x-full');
			setTimeout(function () {
				if (toast.parentElement) toast.remove();
			}, 300);
		}, 5000);
	}

	function initToastClose() {
		var toastContainer = document.getElementById('toast-container');
		if (!toastContainer) return;
		toastContainer.addEventListener('click', function (event) {
			var closeButton = event.target.closest('[data-toast-close]');
			if (!closeButton) return;
			if (closeButton.parentElement) closeButton.parentElement.remove();
		});
	}

	function initFlashMessages() {
		document.querySelectorAll('[data-flash-message]').forEach(function (item) {
			var message = item.getAttribute('data-message');
			var type = item.getAttribute('data-type') || 'info';
			if (message) showToast(message, type);
		});
	}

	function initHistoryBackLinks() {
		document.querySelectorAll('[data-history-back]').forEach(function (link) {
			link.addEventListener('click', function (event) {
				event.preventDefault();
				var fallbackUrl = link.getAttribute('href');
				var referrer = document.referrer;
				var hasSameOriginReferrer = false;
				if (referrer) {
					try {
						hasSameOriginReferrer = new URL(referrer).origin === window.location.origin;
					} catch (error) {
						hasSameOriginReferrer = false;
					}
				}

				if (window.history.length > 1 && hasSameOriginReferrer) {
					window.history.back();
					return;
				}

				if (fallbackUrl) {
					window.location.assign(fallbackUrl);
				}
			});
		});
	}

	function updateThemeUI(mode) {
		var html = document.documentElement;
		var iconSun = document.getElementById('theme-icon-sun');
		var iconMoon = document.getElementById('theme-icon-moon');
		if (!html || !iconSun || !iconMoon) return;
		if (mode === 'dark') {
			html.classList.add('dark');
			iconSun.classList.remove('hidden');
			iconMoon.classList.add('hidden');
		} else {
			html.classList.remove('dark');
			iconSun.classList.add('hidden');
			iconMoon.classList.remove('hidden');
		}
	}

	function initTheme() {
		var saved = localStorage.getItem('theme');
		var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
		var theme = saved || (prefersDark ? 'dark' : 'light');
		updateThemeUI(theme);
		localStorage.setItem('theme', theme);

		var toggle = document.getElementById('theme-toggle');
		if (!toggle) return;
		toggle.addEventListener('click', function () {
			var next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
			updateThemeUI(next);
			localStorage.setItem('theme', next);
			announce(next === 'dark' ? 'Tema oscuro activado' : 'Tema claro activado', 'polite');
		});
	}

	function getFocusableElements(container) {
		if (!container) return [];
		return Array.prototype.slice.call(
			container.querySelectorAll('a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])')
		).filter(function (el) {
			return !el.hasAttribute('hidden') && el.offsetParent !== null;
		});
	}

	function handleModalKeydown(event) {
		var modal = event.currentTarget;
		if (!modal) return;

		if (event.key === 'Escape') {
			event.preventDefault();
			closeModal(modal);
			return;
		}

		if (event.key !== 'Tab') return;

		var focusables = getFocusableElements(modal);
		if (!focusables.length) {
			event.preventDefault();
			modal.focus();
			return;
		}

		var first = focusables[0];
		var last = focusables[focusables.length - 1];
		if (event.shiftKey && document.activeElement === first) {
			event.preventDefault();
			last.focus();
		} else if (!event.shiftKey && document.activeElement === last) {
			event.preventDefault();
			first.focus();
		}
	}

	function openModal(modal, trigger) {
		if (!modal) return;
		if (trigger) {
			modal.__trigger = trigger;
		}
		modal.classList.remove('hidden');
		document.body.classList.add('overflow-hidden');
		modal.setAttribute('aria-hidden', 'false');

		var focusables = getFocusableElements(modal);
		var autofocusTarget = modal.querySelector('[data-modal-initial-focus]');
		setTimeout(function () {
			if (autofocusTarget) autofocusTarget.focus();
			else if (focusables.length) focusables[0].focus();
			else modal.focus();
		}, 0);
	}

	function closeModal(modal) {
		if (!modal) return;
		modal.classList.add('hidden');
		modal.setAttribute('aria-hidden', 'true');
		document.body.classList.remove('overflow-hidden');
		if (modal.__trigger && typeof modal.__trigger.focus === 'function') {
			modal.__trigger.focus();
		}
	}

	function initAccessibleModals() {
		document.querySelectorAll('[data-modal-target]').forEach(function (trigger) {
			trigger.addEventListener('click', function () {
				var selector = trigger.getAttribute('data-modal-target');
				var modal = selector ? document.querySelector(selector) : null;
				openModal(modal, trigger);
			});
		});

		document.querySelectorAll('[data-modal-close]').forEach(function (closer) {
			closer.addEventListener('click', function () {
				var modal = closer.closest('[role="dialog"]');
				closeModal(modal);
			});
		});

		document.querySelectorAll('[role="dialog"]').forEach(function (modal) {
			modal.setAttribute('aria-hidden', modal.classList.contains('hidden') ? 'true' : 'false');
			modal.addEventListener('keydown', handleModalKeydown);
			modal.addEventListener('click', function (event) {
				if (event.target === modal) {
					closeModal(modal);
				}
			});
		});
	}

	function renderTrendBars(container, series, options) {
		if (!container || !Array.isArray(series) || !series.length) return;
		var maxStock = series.reduce(function (max, item) {
			return Math.max(max, Number(item.stock || 0));
		}, 0);

		var maxHeight = (options && options.maxHeight) || 120;
		container.innerHTML = '';

		series.forEach(function (item) {
			var point = document.createElement('div');
			point.className = 'flex-1 min-w-0 flex flex-col items-center justify-end';

			var bar = document.createElement('div');
			var variation = Number(item.variacion || 0);
			var height = maxStock > 0 ? Math.max(Math.round((Number(item.stock || 0) / maxStock) * maxHeight), 2) : 4;
			bar.className = 'w-full rounded-t ' + (variation < 0 ? 'bg-red-400 dark:bg-red-500' : (variation > 0 ? 'bg-teal-500 dark:bg-teal-600' : 'bg-gray-300 dark:bg-gray-600'));
			bar.style.height = height + 'px';
			bar.title = item.fecha + ' | Stock: ' + item.stock + ' | +' + item.entrada + ' / -' + item.salida;

			point.appendChild(bar);
			container.appendChild(point);
		});
	}

	window.AppUX = {
		beginButtonLoading: beginButtonLoading,
		endButtonLoading: endButtonLoading,
		fetchWithTimeout: fetchWithTimeout,
		setNetworkBanner: setNetworkBanner,
		renderTrendBars: renderTrendBars,
		announce: announce,
		openModal: openModal,
		closeModal: closeModal,
		toggleSidebar: toggleSidebar,
		showToast: showToast,
	};
	window.showToast = showToast;

	document.addEventListener('DOMContentLoaded', function () {
		initNetworkBanner();
		initAccessibleModals();
		initSidebar();
		initUserDropdown();
		initToastClose();
		initFlashMessages();
		initHistoryBackLinks();
		initTheme();
	});
})();
