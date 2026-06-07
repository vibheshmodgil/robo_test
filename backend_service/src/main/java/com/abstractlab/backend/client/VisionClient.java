package com.abstractlab.backend.client;

import org.springframework.stereotype.Component;

import com.abstractlab.backend.model.InventoryImageResponse;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;


@Component
public class VisionClient {

    private static final String BASE_URL = "http://host.docker.internal:8003";

    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final ObjectMapper objectMapper = new ObjectMapper();

    // The ONE foreground panel currently on the HUD (inventory step or chat
    // reply). The base "Hi, I am Shiv" panel is the vision default panel and is
    // tracked separately on the Python side, so it never stacks with this one.
    private String currentPanelId;

    // ==================================================================
    //  HIGH-LEVEL HELPERS  (what the modes call)
    // ==================================================================

    /**
     * Show the foreground panel for the current step.
     *
     * If a foreground panel already exists we UPDATE it in place (PUT), so two
     * panels are never alive at the same time -> nothing stacks. Only when there
     * is no panel yet (or the in-place update isn't supported) do we create one,
     * retiring any previous id as a fallback.
     */
    public synchronized void showPanel(String title, String message) {
        String json = panelJson(title, message);

        // 1) Reuse the existing panel -> single panel, no overlap.
        if (currentPanelId != null && tryUpdatePanel(currentPanelId, json)) {
            System.out.println("\nHUD PANEL (updated): " + currentPanelId + "\n");
            return;
        }

        // 2) No panel yet (or update unsupported) -> create, retire the old.
        String oldId = currentPanelId;
        String newId = extractPanelId(createPanel(json));

        if (newId != null) {
            currentPanelId = newId;
            System.out.println("\nHUD PANEL: " + newId + "\n");
        }

        if (oldId != null && !oldId.equals(currentPanelId)) {
            closePanel(oldId);
        }
    }

    /**
     * Pop the base "Hi, I am Shiv" panel. Call this on wakeword (and at startup
     * if you want Shiv idling on screen). It maps to hud_manager.show_welcome()
     * on the vision side and shows whenever no foreground panel is up.
     */
    public synchronized void showWelcome() {
        showWelcome("Hi, I am Shiv");
    }

    public synchronized void showWelcome(String message) {
        try {
            String json = String.format("{ \"message\": \"%s\" }", escape(message));

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/hud/welcome"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            System.out.println("\nWELCOME PANEL:\n" + response.body());
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    /** Close the foreground panel -> the base "Hi, I am Shiv" panel reappears. */
    public synchronized void closeActivePanel() {
        try {
            if (currentPanelId != null) {
                closePanel(currentPanelId);
            }
        } catch (Exception exception) {
            exception.printStackTrace();
        } finally {
            currentPanelId = null;
        }
    }

    /** Legacy name still called by InventoryMode. */
    public synchronized void closeInventoryPanel() {
        closeActivePanel();
    }

    // ==================================================================
    //  INTERNALS
    // ==================================================================

    /** PUT the panel and report whether the vision side accepted it (2xx). */
    private boolean tryUpdatePanel(String panelId, String json) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/hud/panel/" + panelId))
                    .header("Content-Type", "application/json")
                    .PUT(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            return response.statusCode() / 100 == 2;
        } catch (Exception exception) {
            exception.printStackTrace();
            return false;
        }
    }

    private String panelJson(String title, String message) {
        return String.format(
                "{ \"title\": \"%s\", \"message\": \"%s\" }",
                escape(title),
                escape(message)
        );
    }

    private String escape(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    /**
     * POST /hud/panel returns {"panelId":"..."}. Parse it.
     * Falls back to a raw / unquoted body for other shapes.
     */
    private String extractPanelId(String body) {
        if (body == null || body.isBlank()) {
            return null;
        }
        body = body.trim();

        try {
            JsonNode node = objectMapper.readTree(body);
            for (String field : new String[] {"panelId", "panel_id", "id"}) {
                JsonNode value = node.get(field);
                if (value != null && !value.isNull()) {
                    return value.asText();
                }
            }
        } catch (Exception ignored) {
            // not JSON; fall through
        }

        if (body.length() >= 2 && body.startsWith("\"") && body.endsWith("\"")) {
            body = body.substring(1, body.length() - 1);
        }
        return body.isBlank() ? null : body;
    }

    // ==================================================================
    //  RAW HUD ENDPOINTS
    // ==================================================================

    public void setMode(String mode) {
        try {
            String json = String.format("{ \"mode\": \"%s\" }", mode);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/mode"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            System.out.println("\nVISION RESPONSE:\n");
            System.out.println(response.body());
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    public String captureInventoryImage() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/capture"))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            System.out.println("\nIMAGE CAPTURE RESPONSE:\n");

            InventoryImageResponse responseBody = objectMapper.readValue(
                    response.body(), InventoryImageResponse.class);

            return responseBody.getImagePath();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return null;
    }

    public String createPanel(String json) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/hud/panel"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            return response.body();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return null;
    }

    public String updatePanel(String panelId, String json) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/hud/panel/" + panelId))
                    .header("Content-Type", "application/json")
                    .PUT(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            return response.body();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return null;
    }

    public String selectPanel(String panelId, int selected) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(
                            BASE_URL + "/hud/panel/" + panelId + "/select?selected=" + selected))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            return response.body();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return null;
    }

    public String closePanel(String panelId) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + "/hud/panel/" + panelId + "/close"))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request, HttpResponse.BodyHandlers.ofString());

            return response.body();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return null;
    }
}