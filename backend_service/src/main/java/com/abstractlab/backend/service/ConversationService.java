package com.abstractlab.backend.service;

import com.abstractlab.backend.client
        .AudioClient;

import com.abstractlab.backend.client
        .SpeakerClient;

import com.abstractlab.backend.session.WorkflowSession;

import org.springframework.stereotype.Service;

@Service
public class ConversationService {

    private final SpeakerClient
            speakerClient;

    private final AudioClient
            audioClient;

    private final WorkflowSession
            workflowSession;

    public ConversationService(
            SpeakerClient speakerClient,
            AudioClient audioClient,
            WorkflowSession workflowSession
    ) {

        this.speakerClient =
                speakerClient;

        this.audioClient =
                audioClient;

        this.workflowSession =
                workflowSession;
    }

    public void handleWakeword() {

        workflowSession.clear();

        workflowSession
                .setActiveListening(
                        true
                );

        speak(
                "Hey Boss, How may i assist you?"
        );

        audioClient.enableActiveListening();

        }

    public void speak(
                String text
        )
        {
        speakerClient.speakAndWait(
                text
        );
        }
}

