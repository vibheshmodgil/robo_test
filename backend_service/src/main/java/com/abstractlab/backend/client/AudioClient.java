package com.abstractlab.backend.client;

import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@Component
public class AudioClient {

        private static final String BASE_URL = "http://host.docker.internal:8002";

    private final HttpClient client =
            HttpClient.newHttpClient();

    public void enablePassiveListening() {

        sendPost(
                BASE_URL + "/audio/passive"
        );
    }

    public void enableActiveListening() {

        sendPost(
                BASE_URL + "/audio/active"
        );
    }

    public void enableWorkflowMode() {

        sendPost(
                BASE_URL + "/audio/workflow"
        );
    }

    public void startFreshWorkflowListening() {

        sendPost(
                BASE_URL + "/audio/workflow/fresh"
        );
    }

    public void pauseListening() {

        sendPost(
                BASE_URL + "/audio/pause"
        );
        }

        public void resumeListening() {

        sendPost(
                BASE_URL + "/audio/resume"
        );
        }

    private void sendPost(
            String url
    ) {

        try {

            HttpRequest request =
                    HttpRequest.newBuilder()
                            .uri(
                                    URI.create(url)
                            )
                            .POST(
                                    HttpRequest.BodyPublishers
                                            .noBody()
                            )
                            .build();

            client.send(
                    request,
                    HttpResponse
                            .BodyHandlers
                            .ofString()
            );

        } catch (
                Exception exception
        ) {

            exception.printStackTrace();
        }
    }
}