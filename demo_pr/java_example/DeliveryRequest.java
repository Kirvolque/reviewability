package demo.readme;

public record DeliveryRequest(
    String orderId,
    Address destination,
    int packageCount,
    double totalWeightKg,
    double distanceKm,
    int crossDockStops,
    boolean fragile,
    boolean refrigerated,
    boolean returnPickup,
    Priority priority,
    TimeWindow timeWindow,
    AccountTier accountTier
) {
    public boolean isHeavy() {
        return totalWeightKg >= 25.0 || packageCount >= 8;
    }

    public boolean needsSpecialHandling() {
        return fragile
            || refrigerated
            || returnPickup
            || (timeWindow == TimeWindow.EXACT_SLOT && packageCount > 2);
    }

    public boolean requiresScheduledStop() {
        return timeWindow == TimeWindow.EXACT_SLOT
            || (timeWindow == TimeWindow.EVENING && !destination.urbanCore())
            || (returnPickup && fragile)
            || (refrigerated && destination.urbanCore())
            || (priority == Priority.SAME_DAY && destination.requiresExtendedCoverage());
    }

    public boolean allowsDirectHandover() {
        return !fragile
            && !refrigerated
            && destination.urbanCore()
            && timeWindow != TimeWindow.EXACT_SLOT
            && packageCount <= 3;
    }

    public boolean isShortHop() {
        return distanceKm <= 12.0 && destination.urbanCore();
    }

    public enum Priority {
        STANDARD,
        EXPEDITED,
        SAME_DAY
    }

    public enum TimeWindow {
        FLEX,
        BUSINESS_HOURS,
        EVENING,
        EXACT_SLOT
    }

    public enum AccountTier {
        STANDARD,
        PARTNER,
        ENTERPRISE
    }
}
