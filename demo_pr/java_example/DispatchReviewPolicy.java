package demo.readme;

import java.util.ArrayList;
import java.util.List;

public class DispatchReviewPolicy {
    public ReviewDecision evaluate(
        DeliveryRequest request,
        RoutePlan routePlan,
        PricingPolicy.QuoteBreakdown breakdown
    ) {
        int riskPoints = 0;
        List<String> reasons = new ArrayList<>();
        List<String> checkpoints = new ArrayList<>();

        if (routePlan.hubHandoffRequired()) {
            riskPoints += 3;
            reasons.add("Hub handoff introduces coordination risk.");
        }
        if (routePlan.remoteCoverageRequired()) {
            riskPoints += 2;
            reasons.add("Remote coverage requires manual dispatch confirmation.");
        }
        if (request.refrigerated()) {
            riskPoints += 2;
            reasons.add("Temperature-controlled delivery needs cold-chain verification.");
        }
        if (request.fragile()) {
            riskPoints += 1;
            reasons.add("Fragile handling must be reviewed for packing instructions.");
        }
        if (request.priority() == DeliveryRequest.Priority.SAME_DAY) {
            riskPoints += 2;
            reasons.add("Same-day priority compresses planning slack.");
        } else if (request.priority() == DeliveryRequest.Priority.EXPEDITED) {
            riskPoints += 1;
        }

        if (routePlan.travelMinutes() > 180) {
            riskPoints += 2;
            reasons.add("Long travel duration increases timing variance.");
        } else if (routePlan.travelMinutes() > 120) {
            riskPoints += 1;
        }

        if (breakdown.total() > 150.0) {
            riskPoints += 2;
            reasons.add("High-value quote should be verified before release.");
        } else if (breakdown.total() > 90.0) {
            riskPoints += 1;
        }

        if (request.accountTier() == DeliveryRequest.AccountTier.ENTERPRISE && request.returnPickup()) {
            riskPoints += 1;
            reasons.add("Enterprise return pickup requires account-side coordination.");
        }

        for (String reason : reasons) {
            if (reason.contains("temperature") || reason.contains("Remote")) {
                checkpoints.add("Confirm operational owner: " + reason);
            } else if (reason.contains("quote")) {
                checkpoints.add("Verify pricing sign-off: " + reason);
            } else {
                checkpoints.add("Review before dispatch: " + reason);
            }
        }

        ReviewTier tier = classifyTier(riskPoints, routePlan, request);
        boolean manualApprovalRequired = tier == ReviewTier.MANDATORY || request.priority() == DeliveryRequest.Priority.SAME_DAY;

        return new ReviewDecision(
            tier,
            riskPoints,
            manualApprovalRequired,
            reasons,
            checkpoints
        );
    }

    private ReviewTier classifyTier(
        int riskPoints,
        RoutePlan routePlan,
        DeliveryRequest request
    ) {
        if (riskPoints >= 8) {
            return ReviewTier.MANDATORY;
        }
        if (riskPoints >= 5) {
            return routePlan.isMultiStage() ? ReviewTier.MANDATORY : ReviewTier.RECOMMENDED;
        }
        if (request.needsSpecialHandling() || routePlan.isMultiStage()) {
            return ReviewTier.RECOMMENDED;
        }
        return ReviewTier.OPTIONAL;
    }

    public enum ReviewTier {
        OPTIONAL,
        RECOMMENDED,
        MANDATORY
    }

    public record ReviewDecision(
        ReviewTier tier,
        int riskPoints,
        boolean manualApprovalRequired,
        List<String> reasons,
        List<String> checkpoints
    ) {
        public boolean shouldBlockAutoDispatch() {
            return manualApprovalRequired || tier == ReviewTier.MANDATORY;
        }
    }
}
