package com.josrodlop19.javaAnalyzer;

import java.util.List;

import lombok.Getter;
import lombok.Setter;
import spoon.reflect.CtModel;
import spoon.reflect.code.CtInvocation;

@Getter
@Setter
public class StackCallProcessor {
    private CtModel AST;
    private CtInvocation<?> targetInvocation;
    private List<String> callStack;


    
}
