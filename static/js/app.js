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
	};

	document.addEventListener('DOMContentLoaded', initNetworkBanner);
})();
