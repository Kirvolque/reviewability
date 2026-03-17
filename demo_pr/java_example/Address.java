package demo.readme;

public record Address(
    String city,
    String zoneCode,
    boolean urbanCore,
    boolean remoteArea
) {
    public boolean requiresExtendedCoverage() {
        return remoteArea || zoneCode.startsWith("R-");
    }
}
