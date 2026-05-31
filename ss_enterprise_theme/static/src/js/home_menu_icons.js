/** @odoo-module **/

import { registry } from "@web/core/registry";

const homeMenuIconsService = {
    dependencies: ["menu"],
    start(env, { menu }) {
        function getAppData() {
            const iconsByID = {};
            const endMenuIDs = new Set();
            try {
                const apps = menu.getApps();
                for (const app of apps) {
                    if (app.webIconData) {
                        iconsByID[app.id] = { icon: app.webIconData, name: app.name };
                    }
                    const xmlid = app.xmlid || "";
                    if (xmlid === "base.menu_management" || xmlid === "base.menu_administration") {
                        endMenuIDs.add(String(app.id));
                    }
                }
            } catch (e) {}
            return { iconsByID, endMenuIDs };
        }

        function addIcons(popover) {
            const items = popover.querySelectorAll("a.o_app");
            if (!items.length) return;
            const { iconsByID, endMenuIDs } = getAppData();

            const normal = [];
            const end = [];
            items.forEach((item) => {
                const menuID = item.dataset.section || "";
                if (endMenuIDs.has(menuID)) {
                    end.push(item);
                } else {
                    normal.push(item);
                }
            });
            normal.forEach((item) => popover.appendChild(item));
            end.forEach((item) => popover.appendChild(item));

            popover.querySelectorAll("a.o_app").forEach((item) => {
                if (item.querySelector(".et_app_icon")) return;
                const menuID = item.dataset.section || "";
                const appData = iconsByID[menuID];
                const name = item.textContent.trim();
                const iconDiv = document.createElement("div");
                iconDiv.className = "et_app_icon";
                if (appData && appData.icon) {
                    const img = document.createElement("img");
                    img.src = appData.icon;
                    img.alt = name;
                    iconDiv.appendChild(img);
                } else {
                    iconDiv.textContent = name ? name[0].toUpperCase() : "?";
                    iconDiv.classList.add("et_app_icon_letter");
                }
                item.insertBefore(iconDiv, item.firstChild);
            });
        }

        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        const popover = node.classList && node.classList.contains("o_popover")
                            ? node
                            : node.querySelector && node.querySelector(".o_popover");
                        if (popover && popover.querySelector("a.o_app")) {
                            setTimeout(() => addIcons(popover), 10);
                        }
                    }
                }
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
    },
};

registry.category("services").add("home_menu_icons", homeMenuIconsService);

