package demo.readme;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

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
        if (request.refrigerated()
            && request.priority() == DeliveryRequest.Priority.SAME_DAY
            && !request.destination().requiresExtendedCoverage()) {
            throw new IllegalArgumentException("same-day refrigerated routing is not supported");
        }
    }

    private List<String> buildReviewNotes(
        DeliveryRequest request,
        RoutePlan routePlan,
        PricingPolicy.QuoteBreakdown breakdown
    ) {
        boolean requiresDispatchReview =
            routePlan.travelMinutes() > 150
                || routePlan.isMultiStage()
                || breakdown.total() > 120.0;

        List<String> notes = new ArrayList<>(Stream.of(
                noteIf(
                    routePlan.hubHandoffRequired(),
                    "Route requires hub handoff before final delivery."
                ),
                noteIf(
                    routePlan.scheduledStopRequired(),
                    "Dispatch must confirm scheduled-stop handling before release."
                ),
                noteIf(
                    !routePlan.scheduledStopRequired() && routePlan.directHandoverAllowed(),
                    "Direct handover is allowed if driver identity checks pass."
                ),
                noteIf(
                    !routePlan.scheduledStopRequired() && routePlan.directHandoverAllowed(),
                    "Direct handover is allowed if driver identity checks pass."
                )
            )
            .flatMap(stream -> stream)
            .toList());

        if (routePlan.remoteCoverageRequired()) {
            notes.add("Remote coverage surcharge applies.");
        }
        if (request.needsSpecialHandling()) {
            notes.add("Special handling workflow must be scheduled.");
        }
        if (breakdown.accountDiscount() > 0) {
            notes.add("Account discount applied after operational surcharges.");
        }
        if (requiresDispatchReview) {
            notes.add("Dispatch plan should be reviewed for batching, timing, and pricing risk.");
        }

        return notes;
    }

    private Stream<String> noteIf(boolean include, String message) {
        if (!include) {
            return Stream.empty();
        }
        return Stream.of(message);
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
