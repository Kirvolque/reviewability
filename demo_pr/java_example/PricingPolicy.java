package demo.readme;

public class PricingPolicy {
    public QuoteBreakdown buildBreakdown(DeliveryRequest request, RoutePlan routePlan) {
        double baseCharge = computeBaseCharge(request, routePlan);
        double handlingSurcharge = computeHandlingSurcharge(request, routePlan);
        double networkSurcharge = computeNetworkSurcharge(request, routePlan);
        double timeWindowAdjustment = computeTimeWindowAdjustment(request);
        double accountDiscount = computeAccountDiscount(request, baseCharge + handlingSurcharge);

        return new QuoteBreakdown(
            round(baseCharge),
            round(handlingSurcharge),
            round(networkSurcharge),
            round(timeWindowAdjustment),
            round(accountDiscount)
        );
    }

    private double computeBaseCharge(DeliveryRequest request, RoutePlan routePlan) {
        double perKm = switch (routePlan.vehicleMode()) {
            case BIKE -> 0.9;
            case VAN -> 1.4;
            case REFRIGERATED_VAN -> 2.0;
            case LINE_HAUL -> 1.7;
        };

        double base = 8.0 + request.distanceKm() * perKm;
        base += Math.max(0, request.packageCount() - 1) * 1.25;
        base += Math.max(0.0, request.totalWeightKg() - 5.0) * 0.35;
        return base;
    }

    private double computeHandlingSurcharge(DeliveryRequest request, RoutePlan routePlan) {
        double surcharge = 0.0;
        if (request.fragile()) {
            surcharge += 6.5;
        }
        if (request.refrigerated()) {
            surcharge += 9.0;
        }
        if (request.returnPickup()) {
            surcharge += 4.0;
        }
        if (routePlan.temperatureControlRequired()) {
            surcharge += 3.0;
        }
        return surcharge;
    }

    private double computeNetworkSurcharge(DeliveryRequest request, RoutePlan routePlan) {
        double surcharge = routePlan.stopCount() * 1.4;
        if (routePlan.hubHandoffRequired()) {
            surcharge += 7.5;
        }
        if (routePlan.remoteCoverageRequired()) {
            surcharge += 12.0;
        }
        if (request.priority() == DeliveryRequest.Priority.SAME_DAY) {
            surcharge += 10.0;
        } else if (request.priority() == DeliveryRequest.Priority.EXPEDITED) {
            surcharge += 4.5;
        }
        return surcharge;
    }

    private double computeTimeWindowAdjustment(DeliveryRequest request) {
        return switch (request.timeWindow()) {
            case FLEX -> 0.0;
            case BUSINESS_HOURS -> 2.5;
            case EVENING -> 5.0;
            case EXACT_SLOT -> 11.0;
        };
    }

    private double computeAccountDiscount(DeliveryRequest request, double subtotal) {
        return switch (request.accountTier()) {
            case STANDARD -> 0.0;
            case PARTNER -> subtotal * 0.05;
            case ENTERPRISE -> subtotal * 0.12;
        };
    }

    private double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }

    public record QuoteBreakdown(
        double baseCharge,
        double handlingSurcharge,
        double networkSurcharge,
        double timeWindowAdjustment,
        double accountDiscount
    ) {
        public double total() {
            return baseCharge
                + handlingSurcharge
                + networkSurcharge
                + timeWindowAdjustment
                - accountDiscount;
        }
    }
}
