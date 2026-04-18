# Style Guide — El Solterito Inventario

> Single source of truth for all UI decisions. **dashboard.html** is the reference template.

---

## Design Tokens

| Token          | Value                                   |
|----------------|-----------------------------------------|
| Primary        | `#0f766e` (teal-700)                    |
| Secondary      | `#f59e0b` (amber-500)                   |
| Font Family    | Inter, sans-serif                       |
| Border Radius  | `0.75rem` (rounded-xl)                  |
| Box Shadow     | `0 1px 2px rgba(0,0,0,0.05)` (shadow-sm) |
| Spacing Scale  | 4px base (`0.25rem`)                    |

---

## CSS Class Reference

All custom classes are defined in `static/css/estilo.css`. Always prefer these over inline Tailwind utilities for the components listed below.

### Buttons

| Class           | Use case                                 |
|-----------------|------------------------------------------|
| `.btn-primary`  | Main action (save, create, filter)       |
| `.btn-secondary`| Cancel, back, non-critical actions       |
| `.btn-danger`   | Delete, cancel (destructive)             |
| `.btn-success`  | Positive confirmations (sales, receive)  |
| `.btn-info`     | Informational actions (edit, view)       |
| `.btn-outline`  | Tertiary/clear actions                   |
| `.btn-sm`       | Compact size modifier (combine with above) |
| `.btn-icon`     | Icon-only button (e.g., delete icon)     |

### Cards

| Class                          | Use case                              |
|--------------------------------|---------------------------------------|
| `.card`                        | Plain container (lists, tables)       |
| `.card-body`                   | Padding helper (`1.5rem`)             |
| `.card-accent`                 | Form/detail card with teal top border |
| `.card-accent.card-accent-blue`  | Blue top border variant             |
| `.card-accent.card-accent-amber` | Amber top border variant            |
| `.card-accent.card-accent-green` | Green top border variant            |
| `.card-accent.card-accent-red`   | Red top border variant              |

### Tables

| Class          | Element   | Purpose                            |
|----------------|-----------|------------------------------------|
| `.table-header`| `<thead>` | Standardized header background + text styling |
| `.table-row`   | `<tr>`    | Hover state for body rows          |

`<th>` elements inside `.table-header` receive padding, font size, weight, color, uppercase, and letter-spacing automatically. Only add alignment overrides (`text-center`, `text-right`) when needed.

### Badges

| Class            | Color   |
|------------------|---------|
| `.badge-success` | Green   |
| `.badge-danger`  | Red     |
| `.badge-warning` | Amber   |
| `.badge-info`    | Blue    |
| `.badge-neutral` | Gray    |

### Alerts

| Class            | Color   |
|------------------|---------|
| `.alert-success` | Green   |
| `.alert-danger`  | Red     |
| `.alert-info`    | Blue    |
| `.alert-warning` | Amber   |

### Layout & Navigation

| Class          | Purpose                               |
|----------------|---------------------------------------|
| `.sidebar-link`| Sidebar navigation items              |
| `.page-header` | Page header container                 |
| `.page-title`  | Main heading text                     |
| `.page-subtitle`| Secondary description text           |
| `.pagination`  | Pagination nav wrapper                |

---

## Template Patterns

### Page Header
```html
<div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
        <h2 class="text-2xl font-bold text-gray-800 dark:text-white">Title</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Subtitle</p>
    </div>
    <a href="..." class="btn-primary">
        <svg ...>...</svg> Action
    </a>
</div>
```

### Form Card
```html
<div class="card-accent p-6">
    <form method="post" novalidate>
        {% csrf_token %}
        {% if form.errors %}
        <div class="alert-danger mb-6">
            <p class="font-semibold">Por favor corrige los errores:</p>
            {{ form.errors }}
        </div>
        {% endif %}

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for field in form %}
            <div>
                <label for="{{ field.id_for_label }}" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {{ field.label }}{% if field.field.required %} <span class="text-red-500">*</span>{% endif %}
                </label>
                {{ field }}
                {% if field.errors %}<p class="text-red-500 text-sm mt-1">{{ field.errors.0 }}</p>{% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="mt-8 flex flex-col sm:flex-row sm:space-x-3 space-y-3 sm:space-y-0">
            <button type="submit" class="btn-primary">Guardar</button>
            <a href="..." class="btn-secondary">Cancelar</a>
        </div>
    </form>
</div>
```

### List Table
```html
<div class="card overflow-hidden">
    <table class="w-full text-sm">
        <thead class="table-header">
            <tr>
                <th>Column</th>
                <th class="text-center">Centered</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            {% for item in items %}
            <tr class="table-row">
                <td>{{ item.name }}</td>
                <td class="text-center">
                    <span class="badge badge-success">Active</span>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

### Detail KPI Cards
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="card-accent p-6">
        <h2 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase mb-2">Label</h2>
        <p class="text-xl font-bold text-gray-900 dark:text-gray-100">Value</p>
    </div>
    <div class="card-accent card-accent-blue p-6">...</div>
    <div class="card-accent card-accent-green p-6">...</div>
</div>
```

### Delete Confirmation
```html
<div class="max-w-lg mx-auto card-accent card-accent-red p-8 text-center">
    <h1 class="text-3xl font-bold text-red-600 dark:text-red-400 mb-2">Title</h1>
    <div class="alert-danger mb-8">
        <p>Confirmation message</p>
    </div>
    <form method="post">
        {% csrf_token %}
        <div class="flex flex-col sm:flex-row sm:space-x-3 space-y-3 sm:space-y-0 justify-center">
            <button type="submit" class="btn-danger">Confirm</button>
            <a href="..." class="btn-secondary">Cancel</a>
        </div>
    </form>
</div>
```

---

## Rules

1. **Never use inline card/button/badge/alert styling** — always use the CSS classes from `estilo.css`.
2. **Label margin** is `mb-1`, not `mb-2`.
3. **Required fields** must show a red asterisk: `{% if field.field.required %} <span class="text-red-500">*</span>{% endif %}`.
4. **Button containers** use `mt-8 flex flex-col sm:flex-row sm:space-x-3 space-y-3 sm:space-y-0`.
5. **Table headers** only need alignment overrides on `<th>` — padding, font, color, and text-transform are handled by `.table-header th`.
6. **Dark mode** is handled by the CSS classes. No need for manual `dark:` variants on components with design system classes.
7. **Cards** use `rounded-xl` and `shadow-sm` (not `rounded-lg` / `shadow-md`).
8. **dashboard.html** is the reference design — all pages must match its visual quality.
