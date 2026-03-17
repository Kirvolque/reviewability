package demo.readme;

import java.util.ArrayList;
import java.util.List;

public class DispatchReviewPolicy {
    public ReviewDecision evaluate(
        DeliveryRequest request,
        RoutePlan routePlan,
        PricingPolicy.QuoteBreakdown breakdown
    ) {
        int reviewLoad = 0;
        List<String> reviewReasons = new ArrayList<>();
        List<String> followUpActions = new ArrayList<>();
        boolean sameDayPriority = request.priority() == DeliveryRequest.Priority.SAME_DAY;
        boolean temperatureSensitive = request.refrigerated() || routePlan.temperatureControlRequired();
        boolean remoteOrMultiStage = routePlan.remoteCoverageRequired() || routePlan.isMultiStage();

        if (routePlan.hubHandoffRequired()) {
            reviewLoad += 3;
            reviewReasons.add("Hub handoff introduces coordination risk.");
        }
        if (remoteOrMultiStage) {
            reviewLoad += routePlan.remoteCoverageRequired() ? 2 : 1;
            reviewReasons.add("Remote or multi-stage routing requires manual dispatch confirmation.");
        }
        if (temperatureSensitive) {
            reviewLoad += 2;
            reviewReasons.add("Temperature-controlled delivery needs cold-chain verification.");
        }
        if (request.fragile()) {
            reviewLoad += request.returnPickup() ? 2 : 1;
            reviewReasons.add("Fragile handling must be reviewed for packing instructions.");
        }
        if (sameDayPriority) {
            reviewLoad += 2;
            reviewReasons.add("Same-day priority compresses planning slack.");
        } else if (request.priority() == DeliveryRequest.Priority.EXPEDITED) {
            reviewLoad += 1;
        }

        if (routePlan.travelMinutes() > 210) {
            reviewLoad += 3;
            reviewReasons.add("Very long travel duration increases timing variance.");
        } else if (routePlan.travelMinutes() > 140) {
            reviewLoad += 1;
            reviewReasons.add("Long travel duration increases timing variance.");
        }

        if (breakdown.total() > 160.0) {
            reviewLoad += 2;
            reviewReasons.add("High-value quote should be verified before release.");
        } else if (breakdown.total() > 90.0) {
            reviewLoad += 1;
        }

        if (request.accountTier() == DeliveryRequest.AccountTier.ENTERPRISE && request.returnPickup()) {
            reviewLoad += 1;
            reviewReasons.add("Enterprise return pickup requires account-side coordination.");
        }
        if (sameDayPriority && request.returnPickup()) {
            reviewLoad += 1;
            reviewReasons.add("Same-day return pickup needs dispatch confirmation.");
        }

        for (int index = 0; index < reviewReasons.size(); index++) {
            String reason = reviewReasons.get(index);
            boolean firstPass = index < 2;
            if (reason.contains("temperature") || reason.contains("Remote")) {
                followUpActions.add("Confirm operational owner: " + reason);
            } else if (reason.contains("quote")) {
                followUpActions.add("Verify pricing sign-off: " + reason);
            } else if (firstPass && reason.contains("Same-day")) {
                followUpActions.add("Confirm dispatch window: " + reason);
            } else {
                followUpActions.add("Review before dispatch: " + reason);
            }
        }

        ReviewTier tier = classifyTier(reviewLoad, routePlan, request);
        boolean manualApprovalRequired =
            tier == ReviewTier.MANDATORY
                || sameDayPriority
                || (temperatureSensitive && breakdown.total() > 120.0);

        return new ReviewDecision(
            tier,
            reviewLoad,
            manualApprovalRequired,
            reviewReasons,
            followUpActions
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
