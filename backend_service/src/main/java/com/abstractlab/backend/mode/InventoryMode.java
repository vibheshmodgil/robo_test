package com.abstractlab.backend.mode;

import com.abstractlab.backend.client.AudioClient;
import com.abstractlab.backend.client.LocalAgentClient;
import com.abstractlab.backend.client.SpeakerClient;
import com.abstractlab.backend.client.VisionClient;
import com.abstractlab.backend.entity.InventoryItem;
import com.abstractlab.backend.model.AgentRequest;
import com.abstractlab.backend.model.AgentResponse;
import com.abstractlab.backend.service.InventoryService;
import com.abstractlab.backend.states.InventoryState;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;


@Component
public class InventoryMode implements Mode {

    private final SpeakerClient speakerClient;
    private final VisionClient visionClient;
    private final AudioClient audioClient;
    private final InventoryService inventoryService;
    private final LocalAgentClient localAgentClient;

    private String mode;
    private String method;
    private String currentTitle;
    private List<String> details = new ArrayList<>();

    private InventoryState currentState = InventoryState.IDLE;
    private boolean complete = false;

    // When non-null after completion, the orchestrator switches to this mode.
    private String requestedSwitch;

    public InventoryMode(
            SpeakerClient speakerClient,
            VisionClient visionClient,
            AudioClient audioClient,
            InventoryService inventoryService,
            LocalAgentClient localAgentClient
    ) {
        this.speakerClient = speakerClient;
        this.visionClient = visionClient;
        this.audioClient = audioClient;
        this.inventoryService = inventoryService;
        this.localAgentClient = localAgentClient;
    }

    public void start(String method, String reply) {

        resetWorkflow();
        hidePanel();
        requestedSwitch = null;

        visionClient.setMode("inventory");

        this.mode = "INVENTORY";
        this.method = method;
        this.complete = false;

        if ("SET".equalsIgnoreCase(method)) {
            currentState = InventoryState.WAITING_FOR_DESCRIPTION;
            showPanel("DESCRIBE ITEM", "Tell me about the item");
            speakAndContinueWorkflow(reply);
            return;
        }

        if ("GET".equalsIgnoreCase(method)) {
            currentState = InventoryState.WAITING_FOR_SEARCH;
            showPanel("SEARCH INVENTORY", "What should I find?");
            speakAndContinueWorkflow(reply);
            return;
        }

        currentState = InventoryState.WAITING_FOR_METHOD;
        showPanel("INVENTORY", "Save or retrieve?");
        speakAndContinueWorkflow(reply);
    }

    @Override
    public void handle(String command) {

        if (command == null) {
            return;
        }

        command = command.trim();

        if (command.isBlank()) {
            return;
        }

        if (isCancel(command)) {
            cancelWorkflow();
            return;
        }

        // Let the user leave inventory and go back to a normal conversation.
        if (isSwitchToChat(command)) {
            requestedSwitch = "CHAT";
            complete = true;
            hidePanel();
            resetWorkflow();
            return;
        }

        System.out.println("DEBUG:- curr_method " + method);
        System.out.println("DEBUG:- currentState " + currentState);
        System.out.println("DEBUG:- command " + command);

        switch (currentState) {

            case WAITING_FOR_METHOD ->
                    handle_method(command);

            case WAITING_FOR_DESCRIPTION ->
                    handleDescription(command);

            case WAITING_FOR_SEARCH ->
                    handleInventorySearch(command);

            case WAITING_FOR_IMAGE_CONFIRMATION ->
                    handleImageConfirmation(command);

            case WAITING_FOR_TITLE ->
                    handleTitle(command);

            default -> {
            }
        }
    }

    private void handle_method(String command) {

        try {

            AgentResponse response = callAgent("GET_ACTION", command);

            if (response == null) {
                speakAndContinueWorkflow("Please tell me the method: set or get.");
                return;
            }

            if (response.getMethod() != null) {
                method = response.getMethod();
                System.out.println("DEBUG: method saved " + method);
            }

            if ("SET".equalsIgnoreCase(method)) {
                currentState = InventoryState.WAITING_FOR_DESCRIPTION;
                showPanel("DESCRIBE ITEM", "Tell me about the item");
                speakAndContinueWorkflow("Please provide a description.");
                return;
            }

            if ("GET".equalsIgnoreCase(method)) {
                currentState = InventoryState.WAITING_FOR_SEARCH;
                showPanel("SEARCH INVENTORY", "What should I find?");
                speakAndContinueWorkflow("What should I search for?");
                return;
            }

            currentState = InventoryState.WAITING_FOR_METHOD;
            showPanel("INVENTORY", "Save or retrieve?");
            speakAndContinueWorkflow("Please say set or get.");

        } catch (Exception exception) {
            exception.printStackTrace();
            speakAndContinueWorkflow("Method processing failed. Please say set or get.");
        }
    }

    private void handleDescription(String command) {

        try {

            AgentResponse response = callAgent("GET_DESCRIPTION", command);

            if (response == null) {
                speakAndContinueWorkflow("Please describe the item again.");
                return;
            }

            details.clear();

            if (response.getDescription() != null) {
                details.addAll(response.getDescription());
            }

            System.out.println("\nDESCRIPTION FROM AGENT\n");
            System.out.println(details);

            currentState = InventoryState.WAITING_FOR_TITLE;
            showPanel("NAME ITEM", "What should I call it?");
            speakAndContinueWorkflow("What should I call this item?");

        } catch (Exception exception) {
            exception.printStackTrace();
            speakAndContinueWorkflow("Description processing failed. Please describe the item again.");
        }
    }

    private void handleTitle(String command) {

        if (command.isBlank()) {
            speakAndContinueWorkflow("Please provide a title.");
            return;
        }

        // Normalise the spoken phrase into a clean name before we keep it.
        currentTitle = extractName(command);
        System.out.println("DEBUG: title saved " + currentTitle);

        currentState = InventoryState.WAITING_FOR_IMAGE_CONFIRMATION;
        showPanel("ADD IMAGE?", currentTitle);
        speakAndContinueWorkflow("Do you want to save with an image?");
    }

    private void handleImageConfirmation(String command) {

        try {

            boolean wantsImage = command.toLowerCase().contains("yes");
            String imagePath = null;

            audioClient.pauseListening();
            try {

                if (wantsImage) {
                    showPanel("CAPTURING", "Hold still...");
                    speakerClient.speakAndWait("Capturing image");
                    imagePath = visionClient.captureInventoryImage();
                }

                inventoryService.saveDetailedInventoryItem(
                        currentTitle,
                        details,
                        imagePath
                );

                showPanel("SAVED", currentTitle);
                speakerClient.speakAndWait(
                        imagePath != null
                                ? "Inventory item saved with image"
                                : "Inventory item saved without image"
                );

                hidePanel();
                audioClient.enablePassiveListening();

            } finally {
                audioClient.resumeListening();
            }

            complete = true;
            resetWorkflow();

        } catch (Exception exception) {
            exception.printStackTrace();
            showPanel("SAVE FAILED", "Please try again");
            speakAndReturnPassive("Failed to save inventory item.");
            hidePanel();
            resetWorkflow();
            complete = true;
        }
    }

    private void handleInventorySearch(String command) {

        // Normalise the spoken phrase into a clean search term before the query.
        String term = extractName(command);
        System.out.println("DEBUG: search term " + term);

        InventoryItem item = inventoryService.findInventoryItem(term);

        if (item == null) {
            showPanel("NOT FOUND", "Try again or say cancel");
            speakAndContinueWorkflow("Item not found. Try again or say cancel.");
            return;
        }

        String description = item.getDescription();

        if (description == null || description.isBlank()) {
            description = "I found the item, but it has no description.";
        }

        showPanel("ITEM FOUND", term);
        speakAndReturnPassive(description);

        hidePanel();
        complete = true;
        resetWorkflow();
    }

    private void cancelWorkflow() {
        showPanel("CANCELLED", "Inventory closed");
        speakAndReturnPassive("Cancelling inventory workflow");
        hidePanel();
        resetWorkflow();
        complete = true;
    }

    private void resetWorkflow() {
        currentState = InventoryState.IDLE;
        currentTitle = null;
        details.clear();
    }

    @Override
    public boolean isComplete() {
        return complete;
    }

    public String getRequestedSwitch() {
        return requestedSwitch;
    }

    private boolean isCancel(String command) {
        // Tolerant of punctuation and repeats: "Cancel!", "cancel cancel",
        // "please cancel", "cancel that" all end the workflow.
        String c = command.toLowerCase()
                .replaceAll("[^a-z ]", " ")
                .trim()
                .replaceAll(" +", " ");

        if (c.contains("never mind") || c.contains("nevermind")) {
            return true;
        }
        for (String token : c.split(" ")) {
            if (token.equals("cancel")) {
                return true;
            }
        }
        return false;
    }

    private boolean isSwitchToChat(String command) {
        String c = command.toLowerCase();
        return c.contains("switch to chat")
                || c.contains("switch to conversation")
                || c.contains("conversation mode")
                || c.contains("chat mode")
                || c.contains("talk to me")
                || c.contains("let's talk")
                || c.contains("lets talk")
                || c.contains("just talk");
    }

    // --- vision --------------------------------------------------------

    private void showPanel(String title, String message) {
        try {
            visionClient.showPanel(title, message);
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    private void hidePanel() {
        try {
            visionClient.closeInventoryPanel();
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    // --- agent ---------------------------------------------------------

    private String extractName(String command) {
        try {
            AgentResponse response = callAgent("GET_ITEM_NAME", command);
            if (response != null
                    && response.getReply() != null
                    && !response.getReply().isBlank()) {
                return response.getReply().trim();
            }
        } catch (Exception exception) {
            exception.printStackTrace();
        }
        return command;   // fall back to the raw utterance
    }

    private AgentResponse callAgent(String phase, String userInput) {
        AgentRequest request = new AgentRequest();
        request.setMode(mode);
        request.setMethod(method);
        request.setPhase(phase);
        request.setUserInput(userInput);
        return localAgentClient.processInventory(request);
    }

    // --- speech helpers (each mutes the mic while the speaker is talking) ---

    private void speakAndContinueWorkflow(String text) {
        audioClient.pauseListening();
        try {
            speakerClient.speakAndWait(text);
            audioClient.startFreshWorkflowListening();
        } finally {
            audioClient.resumeListening();
        }
    }

    private void speakAndReturnPassive(String text) {
        audioClient.pauseListening();
        try {
            speakerClient.speakAndWait(text);
            audioClient.enablePassiveListening();
        } finally {
            audioClient.resumeListening();
        }
    }
}