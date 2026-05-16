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
	}

	function initNetworkBanner() {
		setNetworkBanner(navigator.onLine);
		window.addEventListener('online', function () { setNetworkBanner(true); });
		window.addEventListener('offline', function () { setNetworkBanner(false); });
	}

	window.AppUX = {
		beginButtonLoading: beginButtonLoading,
		endButtonLoading: endButtonLoading,
		fetchWithTimeout: fetchWithTimeout,
		setNetworkBanner: setNetworkBanner,
	};

	document.addEventListener('DOMContentLoaded', initNetworkBanner);
})();
