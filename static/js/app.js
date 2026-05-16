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
	};

	document.addEventListener('DOMContentLoaded', function () {
		initNetworkBanner();
		initAccessibleModals();
	});
})();
