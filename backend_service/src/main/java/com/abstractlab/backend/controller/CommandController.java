package com.abstractlab.backend.controller;
 
import com.abstractlab.backend.model.CommandRequest;
import com.abstractlab.backend.service.WorkflowOrchestrator;
 
import org.springframework.web.bind.annotation.*;
 
@RestController
@RequestMapping("/commands")
public class CommandController {
 
    private final WorkflowOrchestrator workflowOrchestrator;
 
    public CommandController(WorkflowOrchestrator workflowOrchestrator) {
        this.workflowOrchestrator = workflowOrchestrator;
    }
 
    @PostMapping
    public String handleCommand(@RequestBody CommandRequest request) {
        workflowOrchestrator.handleCommand(request.getCommand());
        return "command handled";
    }
}
 