package com.abstractlab.backend.client;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

@Component
public class SpeakerClient {

    private final HttpClient client =
            HttpClient.newHttpClient();

    public void speakAndWait(
                   String text
) {

    try {

        ObjectMapper mapper =
                new ObjectMapper();

        Map<String,String> body =
                Map.of(
                        "text",
                        text
                );

        String json =
                mapper.writeValueAsString(
                        body
                );

        HttpRequest request =
                HttpRequest.newBuilder()
                        .uri(
                                URI.create(
                                        "http://host.docker.internal:8004/speak"
                                )
                        )
                        .header(
                                "Content-Type",
                                "application/json"
                        )
                        .POST(
                                HttpRequest
                                        .BodyPublishers
                                        .ofString(
                                                json
                                        )
                        )
                        .build();

        HttpResponse<String> response =
                client.send(
                        request,
                        HttpResponse
                                .BodyHandlers
                                .ofString()
                );

        System.out.println(
                "\nSPEAKER RESPONSE:\n"
        );

        System.out.println(
                response.body()
        );

    } catch (
            Exception exception
    ) {

        exception.printStackTrace();
    }
}}