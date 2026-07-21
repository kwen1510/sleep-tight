package com.sleeptight.heartrate;

import android.content.SharedPreferences;
import android.util.Log;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.protolayout.ResourceBuilders;
import androidx.wear.protolayout.TimelineBuilders;
import androidx.wear.tiles.RequestBuilders;
import androidx.wear.tiles.TileBuilders;
import androidx.wear.tiles.TileService;

import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

public final class SleepTightTileService extends TileService {
    private static final String RESOURCES_VERSION = "1";
    private static final String TAG = "SleepTightTile";

    @Override protected ListenableFuture<TileBuilders.Tile> onTileRequest(RequestBuilders.TileRequest request) {
        Log.i(TAG, "Tile requested");
        SharedPreferences prefs = getSharedPreferences("settings", MODE_PRIVATE);
        String status = prefs.getString("tile_status", "Ready to sync");
        int bpm = prefs.getInt("tile_bpm", 0);
        String schedule = String.format(java.util.Locale.US, "%02d:%02d",
                prefs.getInt("bedtime_hour", 21), prefs.getInt("bedtime_minute", 55));

        ActionBuilders.AndroidActivity activity = new ActionBuilders.AndroidActivity.Builder()
                .setPackageName(getPackageName())
                .setClassName(MainActivity.class.getName())
                .addKeyToExtraMapping("tile_sync", new ActionBuilders.AndroidBooleanExtra.Builder().setValue(true).build())
                .build();
        ModifiersBuilders.Clickable connect = new ModifiersBuilders.Clickable.Builder()
                .setId("sync-data")
                .setOnClick(new ActionBuilders.LaunchAction.Builder().setAndroidActivity(activity).build())
                .build();

        LayoutElementBuilders.Column root = new LayoutElementBuilders.Column.Builder()
                .setWidth(DimensionBuilders.expand())
                .setHeight(DimensionBuilders.expand())
                .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
                .addContent(new LayoutElementBuilders.Spacer.Builder().setHeight(DimensionBuilders.weight(1)).build())
                .addContent(text("SLEEP TIGHT", 15, 0xFFFFA36B, true))
                .addContent(new LayoutElementBuilders.Spacer.Builder().setHeight(DimensionBuilders.dp(8)).build())
                .addContent(text("Daily update  " + schedule, 12, 0xFFB7AFB6, false))
                .addContent(new LayoutElementBuilders.Spacer.Builder().setHeight(DimensionBuilders.dp(8)).build())
                .addContent(text(bpm > 0 ? bpm + " BPM · " + status : status, 12, 0xFFFFF4E6, false))
                .addContent(new LayoutElementBuilders.Spacer.Builder().setHeight(DimensionBuilders.dp(12)).build())
                .addContent(new LayoutElementBuilders.Box.Builder()
                        .setWidth(DimensionBuilders.dp(150))
                        .setHeight(DimensionBuilders.dp(44))
                        .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
                        .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
                        .setModifiers(new ModifiersBuilders.Modifiers.Builder()
                                .setClickable(connect)
                                .setBackground(new ModifiersBuilders.Background.Builder()
                                        .setColor(ColorBuilders.argb(0xFFFF8A54))
                                        .setCorner(new ModifiersBuilders.Corner.Builder()
                                                .setRadius(DimensionBuilders.dp(22)).build())
                                        .build())
                                .build())
                        .addContent(text("SYNC DATA", 14, 0xFF211417, true))
                        .build())
                .addContent(new LayoutElementBuilders.Spacer.Builder().setHeight(DimensionBuilders.weight(1)).build())
                .build();

        TimelineBuilders.Timeline timeline = new TimelineBuilders.Timeline.Builder()
                .addTimelineEntry(new TimelineBuilders.TimelineEntry.Builder()
                        .setLayout(new LayoutElementBuilders.Layout.Builder().setRoot(root).build())
                        .build())
                .build();
        return Futures.immediateFuture(new TileBuilders.Tile.Builder()
                .setResourcesVersion(RESOURCES_VERSION)
                .setFreshnessIntervalMillis(60_000)
                .setTileTimeline(timeline)
                .build());
    }

    private static LayoutElementBuilders.Text text(String value, int size, int color, boolean bold) {
        return new LayoutElementBuilders.Text.Builder()
                .setText(value)
                .setMaxLines(1)
                .setFontStyle(new LayoutElementBuilders.FontStyle.Builder()
                        .setSize(DimensionBuilders.sp(size))
                        .setColor(ColorBuilders.argb(color))
                        .setWeight(bold ? LayoutElementBuilders.FONT_WEIGHT_BOLD : LayoutElementBuilders.FONT_WEIGHT_NORMAL)
                        .build())
                .build();
    }

    @Override protected ListenableFuture<ResourceBuilders.Resources> onTileResourcesRequest(
            RequestBuilders.ResourcesRequest request) {
        return Futures.immediateFuture(new ResourceBuilders.Resources.Builder().setVersion(RESOURCES_VERSION).build());
    }
}
