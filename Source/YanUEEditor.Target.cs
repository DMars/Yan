using UnrealBuildTool;
public class YanUEEditorTarget : TargetRules { public YanUEEditorTarget(TargetInfo Target) : base(Target) { Type = TargetType.Editor; DefaultBuildSettings = BuildSettingsVersion.Latest; ExtraModuleNames.Add("YanUE"); } }
