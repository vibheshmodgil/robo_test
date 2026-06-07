package com.abstractlab.backend.controller;

import com.abstractlab.backend.service
        .ConversationService;

import org.springframework.web.bind.annotation.*;

@RestController
public class WakewordController {

    private final ConversationService
            conversationService;

    public WakewordController(
            ConversationService
                    conversationService
    ) {

        this.conversationService =
                conversationService;
    }

    @PostMapping("/wakeword")
    public String wakewordDetected() {

        conversationService
                .handleWakeword();

        return "wakeword received";
    }
}