package com.abstractlab.backend.client;

import com.abstractlab.backend.model.AgentRequest;
import com.abstractlab.backend.model.AgentResponse;

import tools.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@Component
public class LocalAgentClient {

    private final ObjectMapper objectMapper = new ObjectMapper();

    private final HttpClient httpClient;
    private final String inventoryUrl;
    private final Duration requestTimeout;

    public LocalAgentClient(
            @Value("${agent.inventory-url:http://local-agent-service:8005/inventory/process}")
            String inventoryUrl,
            @Value("${agent.connect-timeout-seconds:3}")
            long connectTimeoutSeconds,
            @Value("${agent.request-timeout-seconds:20}")
            long requestTimeoutSeconds
    ) {
        this.inventoryUrl = inventoryUrl;
        this.requestTimeout = Duration.ofSeconds(requestTimeoutSeconds);
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(connectTimeoutSeconds))
                .build();
    }

    public AgentResponse processInventory(AgentRequest request) {

        try {

            String body = objectMapper.writeValueAsString(request);

            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(inventoryUrl))
                    .timeout(requestTimeout)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(
                    httpRequest,
                    HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() >= 300) {
                System.out.println(
                        "[AGENT] non-2xx status " + response.statusCode()
                                + " body=" + response.body()
                );
                return null;
            }

            return objectMapper.readValue(response.body(), AgentResponse.class);

        } catch (Exception exception) {
            // Bounded by the timeouts above, so a dead/slow agent returns null
            // instead of hanging the request (and leaving the mic paused).
            exception.printStackTrace();
            return null;
        }
    }
}