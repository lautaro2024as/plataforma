(() => {
    const qs = (selector, scope = document) => scope.querySelector(selector);
    const qsa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

    const escapeHtml = (value) => String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    const csrfToken = () => {
        const input = qs('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : "";
    };

    window.showView = function(view) {
        const views = {
            store: "viewStore",
            library: "viewLibrary",
            dev: "viewDevPortal",
            admin: "viewGodPanel"
        };

        Object.values(views).forEach(id => qs("#" + id)?.classList.add("hidden-view"));
        qs("#" + (views[view] || views.store))?.classList.remove("hidden-view");

        qsa("[data-view]").forEach(button => {
            button.classList.remove("bg-slate-800", "text-cyan-400");
            if (button.dataset.view === view) {
                button.classList.add("bg-slate-800", "text-cyan-400");
            }
        });

        const url = new URL(window.location.href);
        url.searchParams.set("view", view);
        history.replaceState({}, "", url);
    };

    window.toggleCartDrawer = function() {
        const drawer = qs("#cartDrawer");
        drawer?.classList.toggle("hidden");
        document.body.classList.toggle("no-scroll", !drawer?.classList.contains("hidden"));
    };

    window.openModal = function(id) {
        qs("#" + id)?.classList.remove("hidden");
        document.body.classList.add("no-scroll");
    };

    window.closeModal = function(id) {
        qs("#" + id)?.classList.add("hidden");
        if (id === "gameDetailModal") {
            document.body.classList.remove("arg-detail-open");
            qs("#gameDetailModal")?.setAttribute("aria-hidden", "true");
        }
        if (!qsa(".modal-backdrop:not(.hidden)").length) {
            document.body.classList.remove("no-scroll");
        }
    };

    window.returnToArgGamesHome = function(event) {
        if (event) event.preventDefault();
        window.location.href = window.ARG_GAMES_URLS?.homeUrl || "/?view=store";
        return false;
    };

    window.switchAuthTab = function(tab) {
        ["login", "regUser", "regDev"].forEach(name => {
            qs("#form" + name.charAt(0).toUpperCase() + name.slice(1))?.classList.add("hidden");
        });

        const target = {
            login: "formLogin",
            regUser: "formRegUser",
            regDev: "formRegDev"
        }[tab];

        qs("#" + target)?.classList.remove("hidden");

        ["login", "regUser", "regDev"].forEach(name => {
            const button = qs("#authTab" + name.charAt(0).toUpperCase() + name.slice(1));
            if (!button) return;
            button.classList.remove("text-cyan-400", "border-cyan-400");
            button.classList.add("text-slate-400");
        });

        const active = qs("#authTab" + tab.charAt(0).toUpperCase() + tab.slice(1));
        active?.classList.add("text-cyan-400", "border-cyan-400");
        active?.classList.remove("text-slate-400");
    };

    window.openAuthModal = function(tab = "login") {
        openModal("authModal");
        switchAuthTab(tab);
    };

    window.closeAuthModal = function() {
        closeModal("authModal");
    };

    window.openPublishGameModal = function() {
        openModal("publishGameModal");
    };

    window.closePublishGameModal = function() {
        closeModal("publishGameModal");
    };

    window.openGameModal = function(gameId) {
        const games = window.ARG_GAMES || [];
        const game = games.find(item => Number(item.id) === Number(gameId));
        const content = qs("#gameDetailContent");
        if (!game || !content) return;

        const price = Number(game.price || 0);
        const original = Number(game.original_price || price);
        const discount = original > price ? Math.round((1 - price / original) * 100) : 0;

        const logo = escapeHtml(window.ARG_GAMES_URLS?.logoUrl || "");
        const home = escapeHtml(window.ARG_GAMES_URLS?.homeUrl || "/?view=store");
        content.innerHTML = `
            <div class="arg-detail-head">
                <a class="arg-detail-logo-link" href="${home}" onclick="return returnToArgGamesHome(event)" title="Volver al inicio de ARG GAMES">
                    <img src="${logo}" alt="ARG GAMES — waifus y logotipo">
                    <span>Click para volver al inicio</span>
                </a>
                <button class="arg-detail-close" onclick="closeModal('gameDetailModal')" aria-label="Cerrar detalle del juego" title="Cerrar">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
            </div>
            <div class="arg-detail-game-cover">
                <img src="${escapeHtml(game.image)}" alt="${escapeHtml(game.title)}">
            </div>
            <div class="arg-detail-game-info">
                <span class="inline-flex self-start px-3 py-1 rounded-sm bg-blue-400/10 border border-blue-300/20 text-blue-100 text-xs font-bold uppercase">${escapeHtml(game.category)}</span>
                <h3>${escapeHtml(game.title)}</h3>
                <p class="text-sm text-slate-300">${escapeHtml(game.description)}</p>
                <p class="text-xs text-purple-200"><i class="fa-solid fa-code mr-1"></i>${escapeHtml(game.developer)}</p>
                <div class="flex items-end gap-3">
                    ${discount ? `<span class="bg-red-500/90 text-white text-xs font-black px-2 py-1 rounded-sm">-${discount}%</span>` : ""}
                    ${discount ? `<span class="text-slate-500 line-through">$ ${original.toFixed(2)} USD</span>` : ""}
                    <span class="text-3xl font-black text-blue-100">$ ${price.toFixed(2)} USD</span>
                </div>
                <div class="flex flex-wrap gap-2 text-xs">
                    <span class="glass-pill rounded-sm px-3 py-2 text-slate-300"><i class="fa-brands fa-steam text-blue-200 mr-1"></i>${escapeHtml(game.key_type)}</span>
                    <span class="glass-pill rounded-sm px-3 py-2 text-amber-200"><i class="fa-solid fa-star mr-1"></i>${escapeHtml(game.rating)}</span>
                </div>
                <form method="post" action="${escapeHtml(window.ARG_GAMES_URLS.cartBase.replace("/0/", "/" + game.id + "/"))}" class="arg-purchase-actions space-y-3">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(csrfToken())}">
                    <label class="block text-xs font-bold text-slate-300">Edición</label>
                    <select name="edition" class="glass-input w-full rounded-sm px-3 py-2.5 text-sm text-slate-100 focus:outline-none">
                        <option value="Estándar">Estándar</option>
                        <option value="Deluxe">Deluxe (+$12.00)</option>
                        <option value="Ultimate">Ultimate (+$28.00)</option>
                    </select>
                    <button type="submit" class="w-full py-3 bg-gradient-to-r from-sky-300 to-blue-500 text-slate-950 font-black rounded-sm">
                        <i class="fa-solid fa-cart-plus mr-1"></i> Agregar al carrito
                    </button>
                </form>
                ${game.can_free ? `
                    <form method="post" action="${escapeHtml(window.ARG_GAMES_URLS.freeKeyBase.replace("/0/", "/" + game.id + "/"))}">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(csrfToken())}">
                        <input type="hidden" name="edition" value="Estándar">
                        <button type="submit" class="w-full py-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-sm">
                            <i class="fa-solid fa-key mr-1"></i> Generar clave gratis propia
                        </button>
                    </form>
                ` : ""}
            </div>`;
        openModal("gameDetailModal");
        document.body.classList.add("arg-detail-open");
        qs("#gameDetailModal")?.setAttribute("aria-hidden", "false");
    };

    window.filterCatalog = function() {
        const input = qs("#searchInput");
        const query = (input?.value || "").trim().toLowerCase();
        const category = qs("#categoryFilter")?.value || "all";
        const sort = qs("#sortSelect")?.value || "popular";
        const cards = qsa(".game-card");
        let visible = cards.filter(card => {
            const title = (card.dataset.title || "").toLowerCase();
            const developer = (card.dataset.developer || "").toLowerCase();
            const cardCategory = card.dataset.category || "";
            return (!query || title.includes(query) || developer.includes(query))
                && (category === "all" || cardCategory === category);
        });

        cards.forEach(card => card.classList.toggle("hidden", !visible.includes(card)));

        const grid = qs("#gamesGrid");
        if (grid) {
            visible.sort((a, b) => {
                if (sort === "price-low") return Number(a.dataset.price) - Number(b.dataset.price);
                if (sort === "price-high") return Number(b.dataset.price) - Number(a.dataset.price);
                if (sort === "rating") return Number(b.dataset.rating) - Number(a.dataset.rating);
                return Number(a.dataset.id) - Number(b.dataset.id);
            });
            visible.forEach(card => grid.appendChild(card));
        }

        const count = qs("#gameCount");
        if (count) count.textContent = `${visible.length} juego(s) disponibles`;
    };

    window.copyKey = async function(key) {
        try {
            await navigator.clipboard.writeText(key);
            window.alert("Clave copiada al portapapeles.");
        } catch {
            window.alert(key);
        }
    };

    document.addEventListener("DOMContentLoaded", () => {
        try {
            const json = qs("#arg-games-data");
            window.ARG_GAMES = json ? JSON.parse(json.textContent) : [];
        } catch {
            window.ARG_GAMES = [];
        }

        window.ARG_GAMES_URLS = {
            homeUrl: qs("#argGamesUrls")?.dataset.homeUrl || "/?view=store",
            logoUrl: qs("#argGamesUrls")?.dataset.logoUrl || "",
            cartBase: qs("#argGamesUrls")?.dataset.cartBase || "",
            freeKeyBase: qs("#argGamesUrls")?.dataset.freeKeyBase || ""
        };

        const initial = document.body.dataset.activeView || "store";
        showView(["store", "library", "dev", "admin"].includes(initial) ? initial : "store");

        const authTab = new URL(window.location.href).searchParams.get("auth");
        if (["login", "regUser", "regDev"].includes(authTab)) {
            openAuthModal(authTab);
        }

        filterCatalog();

        qsa(".modal-backdrop").forEach(backdrop => {
            backdrop.addEventListener("click", (event) => {
                if (event.target !== backdrop) return;
                backdrop.classList.add("hidden");
                document.body.classList.remove("no-scroll");
            });
        });

        qs("#searchInput")?.addEventListener("input", filterCatalog);
        qs("#categoryFilter")?.addEventListener("change", filterCatalog);
        qs("#sortSelect")?.addEventListener("change", filterCatalog);
    });
})();
