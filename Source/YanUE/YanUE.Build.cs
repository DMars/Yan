using UnrealBuildTool;
public class YanUE : ModuleRules { public YanUE(ReadOnlyTargetRules Target) : base(Target) { PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs; PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" }); } }
