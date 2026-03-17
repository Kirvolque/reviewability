package demo.readme;

public class CapacityPlanner {
    public RoutePlan plan(DeliveryRequest request) {
        RoutePlan.VehicleMode mode = chooseVehicleMode(request);
        boolean directHandoverAllowed = request.allowsDirectHandover();
        boolean scheduledStopRequired = request.requiresScheduledStop() || !directHandoverAllowed;
        int routeStops = estimateStopCount(request, mode, scheduledStopRequired, directHandoverAllowed);
        int travelMinutes = estimateTravelMinutes(
            request,
            mode,
            routeStops,
            scheduledStopRequired,
            directHandoverAllowed
        );
        boolean hubHandoffRequired = needsHubHandoff(
            request,
            mode,
            routeStops,
            scheduledStopRequired,
            directHandoverAllowed
        );
        boolean remoteCoverageRequired =
            request.destination().requiresExtendedCoverage() || request.priority() == DeliveryRequest.Priority.SAME_DAY;
        boolean temperatureControlRequired =
            request.refrigerated() || (scheduledStopRequired && request.destination().urbanCore());

        return new RoutePlan(
            mode,
            routeStops,
            travelMinutes,
            scheduledStopRequired,
            directHandoverAllowed,
            hubHandoffRequired,
            temperatureControlRequired,
            remoteCoverageRequired
        );
    }

    private RoutePlan.VehicleMode chooseVehicleMode(DeliveryRequest request) {
        if (request.refrigerated()) {
            return RoutePlan.VehicleMode.REFRIGERATED_VAN;
        }
        if (request.destination().requiresExtendedCoverage()
            || request.distanceKm() > 80.0
            || (request.priority() == DeliveryRequest.Priority.SAME_DAY && request.packageCount() > 4)) {
            return RoutePlan.VehicleMode.LINE_HAUL;
        }
        if (request.isShortHop() && !request.isHeavy() && request.allowsDirectHandover()) {
            return RoutePlan.VehicleMode.BIKE;
        }
        return RoutePlan.VehicleMode.VAN;
    }

    private int estimateStopCount(
        DeliveryRequest request,
        RoutePlan.VehicleMode mode,
        boolean scheduledStopRequired,
        boolean directHandoverAllowed
    ) {
        int baseStops = 1 + request.crossDockStops() + (request.returnPickup() ? 1 : 0);
        if (mode == RoutePlan.VehicleMode.LINE_HAUL) {
            baseStops += 2;
        }
        if (scheduledStopRequired) {
            baseStops += mode == RoutePlan.VehicleMode.BIKE ? 0 : 1;
        }
        if (!directHandoverAllowed && request.destination().urbanCore()) {
            baseStops += 1;
        }
        baseStops += request.packageCount() >= 10 ? 1 : 0;
        return baseStops;
    }

    private int estimateTravelMinutes(
        DeliveryRequest request,
        RoutePlan.VehicleMode mode,
        int stopCount,
        boolean scheduledStopRequired,
        boolean directHandoverAllowed
    ) {
        double speedKmh = switch (mode) {
            case BIKE -> 16.0;
            case VAN -> 32.0;
            case REFRIGERATED_VAN -> 28.0;
            case LINE_HAUL -> 52.0;
        };

        double travelMinutes = request.distanceKm() / speedKmh * 60.0;
        double serviceMinutes = stopCount * 9.0;

        if (request.fragile()) {
            serviceMinutes += request.returnPickup() ? 10.0 : 8.0;
        }
        if (request.timeWindow() == DeliveryRequest.TimeWindow.EXACT_SLOT) {
            serviceMinutes += directHandoverAllowed ? 8.0 : 12.0;
        } else if (scheduledStopRequired) {
            serviceMinutes += 10.0;
        } else if (!directHandoverAllowed) {
            serviceMinutes += 6.0;
        }
        if (request.accountTier() == DeliveryRequest.AccountTier.ENTERPRISE
            && request.destination().urbanCore()) {
            serviceMinutes += 4.0;
        }
        if (request.destination().urbanCore() && mode != RoutePlan.VehicleMode.BIKE) {
            travelMinutes += 14.0;
        }

        return (int) Math.ceil(travelMinutes + serviceMinutes);
    }

    private boolean needsHubHandoff(
        DeliveryRequest request,
        RoutePlan.VehicleMode mode,
        int stopCount,
        boolean scheduledStopRequired,
        boolean directHandoverAllowed
    ) {
        if (mode == RoutePlan.VehicleMode.LINE_HAUL) {
            return true;
        }
        if (scheduledStopRequired && request.distanceKm() > (directHandoverAllowed ? 22.0 : 18.0)) {
            return true;
        }
        if ((request.refrigerated() || request.priority() == DeliveryRequest.Priority.SAME_DAY)
            && request.distanceKm() > 25.0) {
            return true;
        }
        return (stopCount >= 5 && request.destination().urbanCore())
            || (!directHandoverAllowed && request.timeWindow() == DeliveryRequest.TimeWindow.EVENING);
    }
}
