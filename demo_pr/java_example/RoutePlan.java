package demo.readme;

public record RoutePlan(
    VehicleMode vehicleMode,
    int stopCount,
    int travelMinutes,
    boolean hubHandoffRequired,
    boolean temperatureControlRequired,
    boolean remoteCoverageRequired
) {
    public boolean isMultiStage() {
        return hubHandoffRequired || stopCount >= 4;
    }

    public enum VehicleMode {
        BIKE,
        VAN,
        REFRIGERATED_VAN,
        LINE_HAUL
    }
}
