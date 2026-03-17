package demo.readme;

public record RoutePlan(
    VehicleMode vehicleMode,
    int stopCount,
    int travelMinutes,
    boolean scheduledStopRequired,
    boolean directHandoverAllowed,
    boolean hubHandoffRequired,
    boolean temperatureControlRequired,
    boolean remoteCoverageRequired
) {
    public boolean isMultiStage() {
        return scheduledStopRequired || hubHandoffRequired || remoteCoverageRequired || stopCount >= 4;
    }

    public enum VehicleMode {
        BIKE,
        VAN,
        REFRIGERATED_VAN,
        LINE_HAUL
    }
}
