package com.abstractlab.backend.service;

import com.abstractlab.backend.client.LocalAgentClient;
import com.abstractlab.backend.mode.ConversationMode;
import com.abstractlab.backend.mode.InventoryMode;
import com.abstractlab.backend.mode.Mode;
import com.abstractlab.backend.model.AgentRequest;
import com.abstractlab.backend.model.AgentResponse;
import com.abstractlab.backend.session.WorkflowSession;

import org.springframework.stereotype.Service;


@Service
public class WorkflowOrchestrator {

    private final WorkflowSession workflowSession;
    private final InventoryMode inventoryMode;
    private final ConversationMode conversationMode;
    private final LocalAgentClient localAgentClient;

    public WorkflowOrchestrator(
            WorkflowSession workflowSession,
            LocalAgentClient localAgentClient,
            InventoryMode inventoryMode,
            ConversationMode conversationMode
    ) {
        this.workflowSession = workflowSession;
        this.localAgentClient = localAgentClient;
        this.inventoryMode = inventoryMode;
        this.conversationMode = conversationMode;
    }

    public void handleCommand(String command) {

        System.out.println("\nCOMMAND : " + command);

        // ============================================================
        // ACTIVE MODE
        // ============================================================
        if (workflowSession.hasActiveMode()) {

            Mode active = workflowSession.getActiveMode();

            // While CHATTING, let the user jump into inventory. We only
            // re-classify when the turn hints at inventory, so normal chit-chat
            // doesn't pay for an extra LLM call every turn.
            if (active instanceof ConversationMode && looksInventoryish(command)) {

                AgentResponse cls = createInitial(command);
                String mode = cls == null || cls.getMode() == null ? "" : cls.getMode().trim();

                if ("INVENTORY".equalsIgnoreCase(mode)) {
                    System.out.println("\nCONVERSATION -> switching to INVENTORY\n");
                    startInventory(cls.getMethod(), cls.getReply());
                    return;
                }
            }

            active.handle(command);

            if (active.isComplete()) {

                // A mode can ask to hand off (e.g. inventory -> chat).
                String next = (active instanceof InventoryMode inv)
                        ? inv.getRequestedSwitch()
                        : null;

                workflowSession.clear();

                if ("CHAT".equalsIgnoreCase(next)) {
                    System.out.println("\nINVENTORY -> switching to CONVERSATION\n");
                    workflowSession.setActiveMode(conversationMode);
                    conversationMode.start(null, "Sure, let's talk. What's on your mind?");
                }
            }
            return;
        }

        // ============================================================
        // NO ACTIVE MODE -> classify + route
        // ============================================================
        AgentResponse response = createInitial(command);

        if (response == null) {
            System.out.println("\nAGENT RESPONSE NULL\n");
            return;
        }

        String mode = response.getMode() == null ? "" : response.getMode().trim();

        if ("INVENTORY".equalsIgnoreCase(mode)) {
            startInventory(response.getMethod(), response.getReply());
            return;
        }

        System.out.println("\nNON-INVENTORY -> starting conversation\n");
        workflowSession.setActiveMode(conversationMode);
        conversationMode.start(command, response.getReply());
    }

    private void startInventory(String method, String reply) {
        workflowSession.setActiveMode(inventoryMode);
        System.out.println( "CALLING inventoryMode.start()"
);
        inventoryMode.start(method, reply);
    }

    // Cheap pre-filter so we don't classify every chat turn.
    private boolean looksInventoryish(String command) {
        if (command == null) {
            return false;
        }
        String c = command.toLowerCase();
        return c.contains("inventory")
                || c.contains("save")
                || c.contains("store")
                || c.contains("add ")
                || c.contains("create")
                || c.contains("get ")
                || c.contains("find")
                || c.contains("search")
                || c.contains("retrieve")
                || c.contains("look up")
                || c.contains("lookup");
    }

    public AgentResponse createInitial(String command) {

        AgentRequest request = new AgentRequest();
        request.setUserInput(command);
        request.setPhase("GET_ACTION");

        AgentResponse response = localAgentClient.processInventory(request);

        if (response != null) {
            System.out.println(response.toString());
        }
        return response;
    }
}