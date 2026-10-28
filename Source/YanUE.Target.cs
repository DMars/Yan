using UnrealBuildTool;
public class YanUETarget : TargetRules { public YanUETarget(TargetInfo Target) : base(Target) { Type = TargetType.Game; DefaultBuildSettings = BuildSettingsVersion.Latest; ExtraModuleNames.Add("YanUE"); } }
