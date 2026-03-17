package demo.readme;

public class CapacityPlanner {
    public RoutePlan plan(DeliveryRequest request) {
        RoutePlan.VehicleMode mode = chooseVehicleMode(request);
        int stopCount = estimateStopCount(request, mode);
        int travelMinutes = estimateTravelMinutes(request, mode, stopCount);
        boolean hubHandoffRequired = needsHubHandoff(request, mode, stopCount);
        boolean temperatureControlRequired = request.refrigerated();
        boolean remoteCoverageRequired = request.destination().requiresExtendedCoverage();

        return new RoutePlan(
            mode,
            stopCount,
            travelMinutes,
            hubHandoffRequired,
            temperatureControlRequired,
            remoteCoverageRequired
        );
    }

    private RoutePlan.VehicleMode chooseVehicleMode(DeliveryRequest request) {
        if (request.refrigerated()) {
            return RoutePlan.VehicleMode.REFRIGERATED_VAN;
        }
        if (request.destination().requiresExtendedCoverage() || request.distanceKm() > 80.0) {
            return RoutePlan.VehicleMode.LINE_HAUL;
        }
        if (request.isShortHop() && !request.isHeavy()) {
            return RoutePlan.VehicleMode.BIKE;
        }
        return RoutePlan.VehicleMode.VAN;
    }

    private int estimateStopCount(DeliveryRequest request, RoutePlan.VehicleMode mode) {
        int baseStops = 1 + request.crossDockStops();
        if (mode == RoutePlan.VehicleMode.LINE_HAUL) {
            baseStops += 2;
        }
        if (request.returnPickup()) {
            baseStops += 1;
        }
        if (request.packageCount() >= 10) {
            baseStops += 1;
        }
        return baseStops;
    }

    private int estimateTravelMinutes(
        DeliveryRequest request,
        RoutePlan.VehicleMode mode,
        int stopCount
    ) {
        double speedKmh = switch (mode) {
            case BIKE -> 16.0;
            case VAN -> 32.0;
            case REFRIGERATED_VAN -> 28.0;
            case LINE_HAUL -> 52.0;
        };

        double travel = request.distanceKm() / speedKmh * 60.0;
        double service = stopCount * 9.0;

        if (request.fragile()) {
            service += 8.0;
        }
        if (request.timeWindow() == DeliveryRequest.TimeWindow.EXACT_SLOT) {
            service += 12.0;
        }
        if (request.destination().urbanCore() && mode != RoutePlan.VehicleMode.BIKE) {
            travel += 14.0;
        }

        return (int) Math.ceil(travel + service);
    }

    private boolean needsHubHandoff(
        DeliveryRequest request,
        RoutePlan.VehicleMode mode,
        int stopCount
    ) {
        if (mode == RoutePlan.VehicleMode.LINE_HAUL) {
            return true;
        }
        if (request.refrigerated() && request.distanceKm() > 25.0) {
            return true;
        }
        return stopCount >= 5 && request.destination().urbanCore();
    }
}
