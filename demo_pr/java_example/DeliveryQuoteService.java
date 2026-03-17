package demo.readme;

import java.util.ArrayList;
import java.util.List;

public class DeliveryQuoteService {
    private final CapacityPlanner capacityPlanner;
    private final PricingPolicy pricingPolicy;

    public DeliveryQuoteService(CapacityPlanner capacityPlanner, PricingPolicy pricingPolicy) {
        this.capacityPlanner = capacityPlanner;
        this.pricingPolicy = pricingPolicy;
    }

    public QuoteResult quote(DeliveryRequest request) {
        validate(request);

        RoutePlan routePlan = capacityPlanner.plan(request);
        PricingPolicy.QuoteBreakdown breakdown = pricingPolicy.buildBreakdown(request, routePlan);

        return new QuoteResult(
            request.orderId(),
            routePlan,
            breakdown,
            buildReviewNotes(request, routePlan, breakdown)
        );
    }

    private void validate(DeliveryRequest request) {
        if (request.packageCount() <= 0) {
            throw new IllegalArgumentException("packageCount must be positive");
        }
        if (request.totalWeightKg() <= 0) {
            throw new IllegalArgumentException("totalWeightKg must be positive");
        }
        if (request.distanceKm() <= 0) {
            throw new IllegalArgumentException("distanceKm must be positive");
        }
        if (request.refrigerated() && request.priority() == DeliveryRequest.Priority.SAME_DAY) {
            throw new IllegalArgumentException("same-day refrigerated routing is not supported");
        }
    }

    private List<String> buildReviewNotes(
        DeliveryRequest request,
        RoutePlan routePlan,
        PricingPolicy.QuoteBreakdown breakdown
    ) {
        List<String> notes = new ArrayList<>();

        if (routePlan.hubHandoffRequired()) {
            notes.add("Route requires hub handoff before final delivery.");
        }
        if (routePlan.remoteCoverageRequired()) {
            notes.add("Remote coverage surcharge applies.");
        }
        if (request.needsSpecialHandling()) {
            notes.add("Special handling workflow must be scheduled.");
        }
        if (breakdown.accountDiscount() > 0) {
            notes.add("Account discount applied after operational surcharges.");
        }
        if (routePlan.travelMinutes() > 180) {
            notes.add("Long route should be reviewed for dispatch batching.");
        }

        return notes;
    }

    public record QuoteResult(
        String orderId,
        RoutePlan routePlan,
        PricingPolicy.QuoteBreakdown breakdown,
        List<String> reviewNotes
    ) {
        public String summary() {
            return "%s via %s, %d min, total %.2f".formatted(
                orderId,
                routePlan.vehicleMode(),
                routePlan.travelMinutes(),
                breakdown.total()
            );
        }
    }
}
