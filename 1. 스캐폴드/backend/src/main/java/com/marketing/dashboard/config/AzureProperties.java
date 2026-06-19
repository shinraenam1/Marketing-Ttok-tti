package com.marketing.dashboard.config;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "azure.openai")
public record AzureProperties(
        @NotBlank String apiKey,
        @NotBlank String endpoint,
        String deployment
) {
}
