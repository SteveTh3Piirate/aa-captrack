{% extends "allianceauth/base.html" %}

{% block content %}
<div class="container mt-4">

    <h1 class="mb-4">CapTrack Dashboard</h1>

    <style>
        /* Slightly darker card header to match AA dark theme */
        .captrack-card-header {
            background-color: #222;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            border-radius: 0.5rem 0.5rem 0 0;
            padding: 0.75rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .captrack-chevron {
            transition: transform 0.2s ease;
        }

        .collapse.show + .captrack-chevron,
        .captrack-card-header[aria-expanded="true"] .captrack-chevron {
            transform: rotate(90deg);
        }
    </style>

    <!-- Blacklisted Regions -->
    <h3>Blacklisted Regions</h3>
    {% if blacklisted_regions %}
        <ul>
            {% for region in blacklisted_regions %}
                <li>{{ region.name }}</li>
            {% endfor %}
        </ul>
    {% else %}
        <p class="text-muted">No blacklisted regions configured.</p>
    {% endif %}

    <hr>

    <!-- Capitals in Blacklisted Regions -->
    <h3>Capitals in Blacklisted Regions</h3>

    {% if groups %}
        {% for group in groups %}
            {% with collapse_id="captrack-"|add:group.main.character_id %}
            <div class="card mt-4" style="background-color:#111; border:1px solid #444; border-radius:0.5rem;">

                <!-- Clickable header -->
                <div class="captrack-card-header"
                     data-bs-toggle="collapse"
                     data-bs-target="#{{ collapse_id }}"
                     aria-expanded="false">

                    <span>
                        <img src="{{ group.main.portrait_url_128 }}"
                             class="rounded me-2"
                             width="32" height="32">
                        {{ group.main.character_name }}
                    </span>

                    <span class="text-primary captrack-chevron">&#9654;</span>
                </div>

                <!-- Collapsible body -->
                <div id="{{ collapse_id }}" class="collapse">
                    <div class="card-body" style="background-color:#181818; border-radius:0 0 0.5rem 0.5rem;">

                        {% if group.alts %}
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr>
                                        <th>Character</th>
                                        <th>Ship</th>
                                        <th>System</th>
                                        <th>Structure / Station</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for alt in group.alts %}
                                        <tr>
                                            <td>{{ alt.ownership.character.character_name }}</td>
                                            <td>{{ alt.ship_type }}</td>
                                            <td>{{ alt.system }}</td>
                                            <td>{{ alt.structure|default:"(Unknown)" }}</td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        {% else %}
                            <p class="text-muted">No alt characters found.</p>
                        {% endif %}

                    </div>
                </div>

            </div>
            {% endwith %}
        {% endfor %}
    {% else %}
        <p class="text-muted">No capitals found in blacklisted regions.</p>
    {% endif %}

</div>
{% endblock %}
