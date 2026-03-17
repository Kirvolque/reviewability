package demo.readme;

import java.util.function.Function;
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

        return Stream.of(
                note(
                    routePlan.hubHandoffRequired(),
                    "Route requires hub handoff before final delivery."
                ),
                note(
                    routePlan.scheduledStopRequired(),
                    "Dispatch must confirm scheduled-stop handling before release."
                ),
                note(
                    !routePlan.scheduledStopRequired() && routePlan.directHandoverAllowed(),
                    "Direct handover is allowed if driver identity checks pass."
                ),
                note(
                    routePlan.remoteCoverageRequired(),
                    "Remote coverage surcharge applies."
                ),
                note(
                    request.needsSpecialHandling(),
                    "Special handling workflow must be scheduled."
                ),
                note(
                    breakdown.accountDiscount() > 0,
                    "Account discount applied after operational surcharges."
                ),
                note(
                    requiresDispatchReview,
                    "Dispatch plan should be reviewed for batching, timing, and pricing risk."
                )
            )
            .flatMap(Function.identity())
            .toList();
    }

    private Stream<String> note(boolean include, String message) {
        return include ? Stream.of(message) : Stream.empty();
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
