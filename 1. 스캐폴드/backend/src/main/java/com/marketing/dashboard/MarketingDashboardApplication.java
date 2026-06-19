package com.marketing.dashboard;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class MarketingDashboardApplication {

    public static void main(String[] args) {
        SpringApplication.run(MarketingDashboardApplication.class, args);
    }
}
