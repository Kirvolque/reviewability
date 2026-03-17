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
        return fragile || refrigerated || returnPickup;
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
